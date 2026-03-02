import math
import numpy as np


def calculate_max_dir_result(section_max_dirs, function_name, common_name, case_names, use_safety_factor,
                             dir_number, dlc_safety_factor, polar_cov_sigma=None):
    mxy_maxes, safety_factors = zip(
        *[(max_dir.mxy_maxes, max_dir.split_safety_factors) for max_dir in section_max_dirs])
    mxy_maxes = np.asarray(mxy_maxes)
    safety_factors = np.asarray(safety_factors)
    safety_mxy_maxes = np.asarray(mxy_maxes)
    mxy_cov_sigmas = np.zeros(safety_mxy_maxes.shape[1])
    cov = sigma = actual_covs = cov_sigmas = None

    if use_safety_factor:
        safety_mxy_maxes = mxy_maxes * safety_factors

    if polar_cov_sigma is not None:
        cov, sigma, actual_covs, std = polar_cov_sigma
        std_sigmas = std * sigma
        safety_mxy_maxes += std_sigmas * safety_factors
        mxy_cov_sigmas = std_sigmas

    bin_thetas = np.asarray([max_dir.bin_thetas for max_dir in section_max_dirs])
    synchronous = list(zip(*[max_dir.synchronous_timeseries for max_dir in section_max_dirs]))
    safety_intra_mxy_maxes, case_index, intra_thetas, _ = function_name(safety_mxy_maxes, bin_thetas)
    if isinstance(case_index, float) and case_index == math.inf:
        if len(np.unique(safety_factors)) == 1:
            safety_factors = np.repeat(safety_factors[0][0], len(safety_intra_mxy_maxes))
        else:
            intra_mxy_maxes, *_ = function_name(mxy_maxes, bin_thetas)
            safety_factors = (safety_intra_mxy_maxes - mxy_cov_sigmas) / intra_mxy_maxes
        if len(synchronous) > 0:
            synchronous = np.nanmean(np.asarray(synchronous), axis=1)
        case_names = np.repeat(common_name, len(safety_intra_mxy_maxes))
    else:
        grid_index = np.ix_(case_index, np.arange(dir_number))
        safety_factors = np.asarray(safety_factors)[grid_index].diagonal()
        synchronous = np.asarray([np.asarray(sync)[grid_index].diagonal() for sync in synchronous])
        case_names = case_names[case_index]
        if polar_cov_sigma is not None:
            cov_sigmas = np.tile(cov, (len(section_max_dirs), 1))[grid_index].diagonal() * \
                         np.tile(sigma, (len(section_max_dirs), 1))[grid_index].diagonal()
    section = section_max_dirs[0].channel_viewer.section
    return MaxDirResult(section, case_names, safety_intra_mxy_maxes, intra_thetas, safety_factors,
                        channel_viewer=section_max_dirs[0].channel_viewer, synchronous=synchronous,
                        dlc_safety_factor=dlc_safety_factor, cov_sigmas=cov_sigmas, actual_covs=actual_covs)
