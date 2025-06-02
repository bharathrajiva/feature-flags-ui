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

from kubernetes import client, config
from typing import Dict

def patch_flags(project: str, env: str, flags: Dict[str, dict]) -> bool:
    """
    Patch a FeatureFlag custom resource in Kubernetes managed by OpenFeature Operator.

    :param project: Project name (currently unused, included for future logic).
    :param env: The environment name, which is also the namespace (e.g., 'review-mr-23').
    :param flags: A dictionary of flags to patch into the resource.
    :return: True if successful, False otherwise.
    """
    try:
        api = client.CustomObjectsApi()

        group = "core.openfeature.dev"
        version = "v1beta1"
        plural = "featureflags"
        namespace = f"flagd-{env}"
        name = f"{env}-app-flags"

        patch_body = {
            "spec": {
                "flagSpec": {
                    "flags": flags
                }
            }
        }

        print(api.patch_namespaced_custom_object(
            group=group,
            version=version,
            namespace=namespace,
            plural=plural,
            name=name,
            body=patch_body,
        ))
        return True

    except Exception as e:
        print(f"[ERROR] Failed to patch FeatureFlag in namespace '{namespace}': {e}")
        return False
