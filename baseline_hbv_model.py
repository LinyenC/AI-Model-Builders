from __future__ import annotations

import numpy as np

MODEL_METADATA = {'model_name': 'baseline_standard_hbv_fine_process_dsl', 'candidate_mode': 'module_dsl', 'dsl_contract_version': 'hydro_process_dsl_v1', 'source': 'provided_hbv_model_adapted_fine_process_dsl', 'changed_processes': [], 'module_overrides': [], 'modification_summary': 'Baseline HBV represented through fine-grained v0.3.1 process interfaces: precipitation partitioning, snow accumulation, snow melt, PET adjustment, soil recharge, actual ET, percolation, response, and routing.'}

DEFAULT_PARAMETERS = {'tt': 0.0, 'cfmax': 3.0, 'cfr': 0.05, 'cwh': 0.1, 'fc': 200.0, 'beta': 2.0, 'lp': 0.7, 'k0': 0.05, 'k1': 0.03, 'k2': 0.005, 'uzl': 30.0, 'perc': 1.0, 'maxbas': 1.0, 'initial_snowpack': 0.0, 'initial_snow_water': 0.0, 'initial_soil_moisture': 100.0, 'initial_upper_zone': 0.0, 'initial_lower_zone': 0.0}

PARAMETER_BOUNDS = {'tt': [-2.0, 2.0], 'cfmax': [0.5, 8.0], 'cfr': [0.0, 0.2], 'cwh': [0.0, 0.3], 'fc': [50.0, 800.0], 'beta': [0.5, 6.0], 'lp': [0.3, 1.0], 'k0': [0.01, 0.8], 'k1': [0.001, 0.5], 'k2': [0.0001, 0.1], 'uzl': [0.0, 100.0], 'perc': [0.0, 10.0], 'maxbas': [1.0, 7.0]}

CALIBRATION_PARAMETERS = ['tt', 'cfmax', 'cfr', 'cwh', 'fc', 'beta', 'lp', 'k0', 'k1', 'k2', 'uzl', 'perc', 'maxbas']

def precip_partition_step(p, temp, state, par):
    tt = float(par["tt"])
    precipitation = max(float(p), 0.0)
    if float(temp) < tt:
        rainfall = 0.0
        snowfall = precipitation
    else:
        rainfall = precipitation
        snowfall = 0.0
    return {"rainfall": rainfall, "snowfall": snowfall, "fluxes": {"rainfall": rainfall, "snowfall": snowfall}}

def snow_accumulation_step(snowfall, state, par):
    snowpack = max(float(state["snowpack"]), 0.0) + max(float(snowfall), 0.0)
    snow_water = max(float(state["snow_water"]), 0.0)
    return {"snowpack": snowpack, "snow_water": snow_water, "fluxes": {"snowfall": max(float(snowfall), 0.0)}}

def snow_melt_step(rainfall, temp, state, par):
    tt = float(par["tt"])
    cfmax = float(par["cfmax"])
    cfr = float(par["cfr"])
    cwh = float(par["cwh"])
    snowpack = max(float(state["snowpack"]), 0.0)
    snow_water = max(float(state["snow_water"]), 0.0)
    rain = max(float(rainfall), 0.0)
    if float(temp) > tt:
        melt = min(snowpack, cfmax * max(float(temp) - tt, 0.0))
        refreezing = 0.0
        snowpack -= melt
        snow_water += melt + rain
    else:
        refreezing = min(snow_water, cfr * cfmax * max(tt - float(temp), 0.0))
        snow_water -= refreezing
        snowpack += refreezing
        melt = 0.0
        snow_water += rain
    max_liquid_water = cwh * snowpack
    if snow_water > max_liquid_water:
        liquid_input = snow_water - max_liquid_water
        snow_water = max_liquid_water
    else:
        liquid_input = 0.0
    return {
        "liquid_input": max(liquid_input, 0.0),
        "snowpack": max(snowpack, 0.0),
        "snow_water": max(snow_water, 0.0),
        "fluxes": {"rainfall": rain, "melt": melt, "refreezing": refreezing, "liquid_input": liquid_input},
    }

def pet_adjustment_step(potential_et, temp, day_index, state, par):
    adjusted_pet = max(float(potential_et), 0.0)
    return {"adjusted_pet": adjusted_pet, "fluxes": {"adjusted_pet": adjusted_pet}}

def soil_recharge_step(liquid_input, state, par):
    fc = float(par["fc"])
    beta = float(par["beta"])
    soil_moisture = max(float(state["soil_moisture"]), 0.0)
    water_input = max(float(liquid_input), 0.0)
    soil_fraction = min(max(soil_moisture / max(fc, 1.0e-9), 0.0), 1.0)
    recharge = water_input * soil_fraction ** beta
    soil_moisture += water_input - recharge
    if soil_moisture > fc:
        excess = soil_moisture - fc
        soil_moisture = fc
        recharge += excess
    else:
        excess = 0.0
    return {
        "recharge": max(recharge, 0.0),
        "soil_moisture": max(soil_moisture, 0.0),
        "fluxes": {"recharge": recharge, "soil_excess": excess},
    }

def actual_et_step(adjusted_pet, state, par):
    fc = float(par["fc"])
    lp = float(par["lp"])
    soil_moisture = max(float(state["soil_moisture"]), 0.0)
    et_reduction = min(soil_moisture / max(lp * fc, 1.0e-9), 1.0)
    actual_et = min(soil_moisture, max(float(adjusted_pet), 0.0) * et_reduction)
    soil_moisture -= actual_et
    return {
        "actual_et": max(actual_et, 0.0),
        "soil_moisture": max(soil_moisture, 0.0),
        "fluxes": {"actual_et": actual_et},
    }

def percolation_step(recharge, state, par):
    perc = float(par["perc"])
    upper_zone = max(float(state["upper_zone"]), 0.0) + max(float(recharge), 0.0)
    lower_zone = max(float(state["lower_zone"]), 0.0)
    percolation = min(upper_zone, max(perc, 0.0))
    upper_zone -= percolation
    lower_zone += percolation
    return {
        "upper_zone": max(upper_zone, 0.0),
        "lower_zone": max(lower_zone, 0.0),
        "fluxes": {"percolation": percolation},
    }

def response_step(state, par):
    k0 = float(par["k0"])
    k1 = float(par["k1"])
    k2 = float(par["k2"])
    uzl = float(par["uzl"])
    upper_zone = max(float(state["upper_zone"]), 0.0)
    lower_zone = max(float(state["lower_zone"]), 0.0)
    q0 = k0 * max(upper_zone - uzl, 0.0)
    q1 = k1 * upper_zone
    q2 = k2 * lower_zone
    q_upper = min(upper_zone, q0 + q1)
    if q0 + q1 > 0.0:
        upper_scale = q_upper / (q0 + q1)
        q0 *= upper_scale
        q1 *= upper_scale
    upper_zone -= q0 + q1
    q2 = min(lower_zone, q2)
    lower_zone -= q2
    runoff = q0 + q1 + q2
    return {
        "runoff": max(runoff, 0.0),
        "upper_zone": max(upper_zone, 0.0),
        "lower_zone": max(lower_zone, 0.0),
        "fluxes": {"q0": q0, "q1": q1, "q2": q2, "runoff": runoff},
    }

def routing_transform(runoff, par):
    q = np.asarray(runoff, dtype=float)
    maxbas = float(par["maxbas"])
    weights = triangular_weights(maxbas)
    if len(weights) == 1:
        qsim = q.copy()
    else:
        qsim = np.convolve(q, weights, mode="full")[: len(q)]
    routing_storage = max(0.0, float(np.sum(q)) - float(np.sum(qsim)))
    return {"qsim": qsim, "routing_storage": routing_storage}



def simulate_hbv(precipitation, temperature, pet, params):
    p_arr = np.asarray(precipitation, dtype=float)
    t_arr = np.asarray(temperature, dtype=float)
    pet_arr = np.asarray(pet, dtype=float)
    if p_arr.shape != t_arr.shape or p_arr.shape != pet_arr.shape:
        raise ValueError("precipitation, temperature, and pet must have the same shape")
    if p_arr.ndim != 1:
        raise ValueError("input arrays must be one-dimensional")
    if p_arr.size == 0:
        raise ValueError("input arrays must not be empty")
    if not np.all(np.isfinite(p_arr)) or not np.all(np.isfinite(t_arr)) or not np.all(np.isfinite(pet_arr)):
        raise ValueError("input arrays must be finite")
    if np.any(p_arr < 0.0) or np.any(pet_arr < 0.0):
        raise ValueError("precipitation and pet must be non-negative")

    par = DEFAULT_PARAMETERS.copy()
    for key, value in params.items():
        par[key] = float(value)
    _validate_parameters(par)

    snow_state = {
        "snowpack": max(float(par["initial_snowpack"]), 0.0),
        "snow_water": max(float(par["initial_snow_water"]), 0.0),
    }
    soil_state = {"soil_moisture": max(float(par["initial_soil_moisture"]), 0.0)}
    response_state = {
        "upper_zone": max(float(par["initial_upper_zone"]), 0.0),
        "lower_zone": max(float(par["initial_lower_zone"]), 0.0),
    }
    initial_storage = (
        snow_state["snowpack"]
        + snow_state["snow_water"]
        + soil_state["soil_moisture"]
        + response_state["upper_zone"]
        + response_state["lower_zone"]
    )

    runoff_before_routing = np.zeros_like(p_arr, dtype=float)
    actual_et = np.zeros_like(p_arr, dtype=float)
    snow_storage = np.zeros_like(p_arr, dtype=float)
    soil_series = np.zeros_like(p_arr, dtype=float)
    groundwater_storage = np.zeros_like(p_arr, dtype=float)

    total_p = 0.0
    total_et = 0.0
    negative_flux_count = 0
    state_violation_count = 0

    for index in range(p_arr.size):
        p = float(p_arr[index])
        temp = float(t_arr[index])
        potential_et = float(pet_arr[index])
        total_p += p

        partition = precip_partition_step(p, temp, {}, par)
        rainfall = _required_float(partition, "rainfall")
        snowfall = _required_float(partition, "snowfall")

        snow_acc = snow_accumulation_step(snowfall, snow_state, par)
        snow_state["snowpack"] = _required_float(snow_acc, "snowpack")
        snow_state["snow_water"] = _required_float(snow_acc, "snow_water")

        snow_melt = snow_melt_step(rainfall, temp, snow_state, par)
        liquid_input = _required_float(snow_melt, "liquid_input")
        snow_state["snowpack"] = _required_float(snow_melt, "snowpack")
        snow_state["snow_water"] = _required_float(snow_melt, "snow_water")

        pet_result = pet_adjustment_step(potential_et, temp, index, soil_state, par)
        adjusted_pet = _required_float(pet_result, "adjusted_pet")

        soil_result = soil_recharge_step(liquid_input, soil_state, par)
        recharge = _required_float(soil_result, "recharge")
        soil_state["soil_moisture"] = _required_float(soil_result, "soil_moisture")

        et_result = actual_et_step(adjusted_pet, soil_state, par)
        eta = _required_float(et_result, "actual_et")
        soil_state["soil_moisture"] = _required_float(et_result, "soil_moisture")

        perc_result = percolation_step(recharge, response_state, par)
        response_state["upper_zone"] = _required_float(perc_result, "upper_zone")
        response_state["lower_zone"] = _required_float(perc_result, "lower_zone")

        response_result = response_step(response_state, par)
        runoff = _required_float(response_result, "runoff")
        response_state["upper_zone"] = _required_float(response_result, "upper_zone")
        response_state["lower_zone"] = _required_float(response_result, "lower_zone")

        for result in (partition, snow_acc, snow_melt, pet_result, soil_result, et_result, perc_result, response_result):
            negative_flux_count += _count_negative_fluxes(result.get("fluxes", {}))
        if rainfall < -1.0e-10 or snowfall < -1.0e-10 or liquid_input < -1.0e-10 or recharge < -1.0e-10 or eta < -1.0e-10 or runoff < -1.0e-10:
            negative_flux_count += 1

        if (
            snow_state["snowpack"] < -1.0e-10
            or snow_state["snow_water"] < -1.0e-10
            or soil_state["soil_moisture"] < -1.0e-10
            or response_state["upper_zone"] < -1.0e-10
            or response_state["lower_zone"] < -1.0e-10
        ):
            state_violation_count += 1

        runoff_before_routing[index] = max(runoff, 0.0)
        actual_et[index] = max(eta, 0.0)
        snow_storage[index] = max(snow_state["snowpack"], 0.0) + max(snow_state["snow_water"], 0.0)
        soil_series[index] = max(soil_state["soil_moisture"], 0.0)
        groundwater_storage[index] = max(response_state["upper_zone"], 0.0) + max(response_state["lower_zone"], 0.0)
        total_et += max(eta, 0.0)

    routing_result = routing_transform(runoff_before_routing, par)
    qsim = np.asarray(routing_result["qsim"], dtype=float)
    if qsim.shape != p_arr.shape:
        raise ValueError("routing_transform must return qsim with the same shape as runoff")
    routing_storage = float(routing_result.get("routing_storage", 0.0))
    if routing_storage < -1.0e-10:
        state_violation_count += 1
    if np.any(qsim < -1.0e-10):
        negative_flux_count += 1
    qsim = np.maximum(qsim, 0.0)

    total_q = float(np.sum(qsim))
    final_storage = (
        max(snow_state["snowpack"], 0.0)
        + max(snow_state["snow_water"], 0.0)
        + max(soil_state["soil_moisture"], 0.0)
        + max(response_state["upper_zone"], 0.0)
        + max(response_state["lower_zone"], 0.0)
        + max(routing_storage, 0.0)
    )
    balance_residual = total_p + initial_storage - total_et - total_q - final_storage
    denom = max(total_p + initial_storage, 1.0)
    return {
        "qsim": qsim,
        "actual_et": actual_et,
        "snow_storage": snow_storage,
        "soil_moisture": soil_series,
        "groundwater_storage": groundwater_storage,
        "water_balance_error": float(balance_residual / denom),
        "negative_flux_count": int(negative_flux_count),
        "state_violation_count": int(state_violation_count),
        "routing_storage": float(max(routing_storage, 0.0)),
    }


def _required_float(result, key):
    if key not in result:
        raise KeyError("module result missing key: " + key)
    value = float(result[key])
    if not np.isfinite(value):
        raise ValueError("module result must be finite: " + key)
    return value


def _count_negative_fluxes(fluxes):
    if not isinstance(fluxes, dict):
        return 1
    count = 0
    for value in fluxes.values():
        array = np.asarray(value, dtype=float)
        if not np.all(np.isfinite(array)):
            count += 1
        elif np.any(array < -1.0e-10):
            count += 1
    return count


def _validate_parameters(par):
    for key, value in par.items():
        if not np.isfinite(float(value)):
            raise ValueError("parameter must be finite: " + str(key))
    for key, bound in PARAMETER_BOUNDS.items():
        if key not in par:
            raise ValueError("parameter missing from DEFAULT_PARAMETERS: " + key)
        lower = float(bound[0])
        upper = float(bound[1])
        value = float(par[key])
        if value < lower - 1.0e-12 or value > upper + 1.0e-12:
            raise ValueError("parameter outside bounds: " + key)
    if par["fc"] <= 0.0:
        raise ValueError("fc must be positive")
    if not (0.0 < par["lp"] <= 1.0):
        raise ValueError("lp must be in the interval (0, 1]")


def triangular_weights(maxbas, shape=1.0):
    n = int(round(float(maxbas)))
    if n <= 1:
        return np.array([1.0], dtype=float)
    midpoint = (n + 1.0) / 2.0
    weights = np.zeros(n, dtype=float)
    for idx in range(1, n + 1):
        if idx <= midpoint:
            weights[idx - 1] = idx / midpoint
        else:
            weights[idx - 1] = (n + 1.0 - idx) / midpoint
    weights = weights ** max(float(shape), 0.05)
    weights_sum = float(np.sum(weights))
    if weights_sum <= 0.0:
        return np.array([1.0], dtype=float)
    return weights / weights_sum
