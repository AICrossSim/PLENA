from optuna.integration.botorch import BoTorchSampler, qei_candidates_func

def candidates_with_lengthscale(X, Y, constraints, bounds):
    # This is the default acquisition function generator
    from optuna.integration.botorch import _create_qei_candidates_func
    from optuna.integration.botorch import _model

    # Fit GP model using BoTorch's helper (same as Optuna does internally)
    gp = _model.fit_model(X, Y, bounds)

    # Try to get kernel lengthscale
    try:
        knl = gp.covar_module
        if hasattr(knl, "base_kernel"):
            knl = knl.base_kernel
        lengthscale = knl.lengthscale.detach().cpu().numpy()
        print(f"[DEBUG] Kernel lengthscale: {lengthscale}")
    except Exception as e:
        print(f"[WARN] Could not extract lengthscale: {e}")

    # Now run the default candidate generation
    return qei_candidates_func(X, Y, constraints, bounds)

# Use it when creating the sampler
sampler = BoTorchSampler(candidates_func=candidates_with_lengthscale)
