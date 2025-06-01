from kubernetes import client, config
import jsonpatch
import os

# Automatically detect the environment
if os.getenv("KUBERNETES_SERVICE_HOST"):
    config.load_incluster_config()
else:
    config.load_kube_config()

from kubernetes import client, config
import os

def get_flags(project, env):
    try:
        # Use in-cluster config if running in a Pod
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            config.load_incluster_config()
        else:
            config.load_kube_config()

        api = client.CustomObjectsApi()

        # ✅ Correct group, version, and plural
        group = "core.openfeature.dev"
        version = "v1beta1"
        namespace = f"flagd-{env}"
        plural = "featureflags"
        name = f"{env}-app-flags"

        flags_source = api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=name
        )

        # ✅ Path to flags is now under `spec.flagSpec.flags`
        flags = flags_source.get("spec", {}).get("flagSpec", {}).get("flags", {})
        return flags

    except Exception as e:
        print(f"K8s get error: {e}")
        return None


# def patch_flags(project, env, flags):
#     try:
#         api = client.CustomObjectsApi()

#         # Customize group, version, and plural to match your OpenFeature CRD
#         group = "openfeature.dev"
#         version = "v1alpha1"
#         namespace = env  # Assuming env = namespace
#         plural = "featureflagsources"
#         name = f"{project}-feature-flags"

#         # Prepare patch payload — example assumes flags under spec.flags
#         patch = {
#             "spec": {
#                 "flags": flags
#             }
#         }

#         api.patch_namespaced_custom_object(
#             group=group,
#             version=version,
#             namespace=namespace,
#             plural=plural,
#             name=name,
#             body=patch
#         )
#         return True
#     except Exception as e:
#         print(f"K8s patch error: {e}")
#         return False
