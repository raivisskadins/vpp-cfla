# -----------------------------------------------------------------------------
# Configuration file: my_config.py
# -----------------------------------------------------------------------------
# This file is used to define **user-specific configuration parameters**
# separately from the Jupyter notebook. It allows each user to set their own
# values without modifying the shared notebook or interfering with others.
#
# Usage pattern in the notebook:
#     overwrite = globals().get('my_overwrite', False)
#
# This means:
# - If `my_overwrite` is defined in this config file, its value will be used.
# - If it is not defined, the default value (`False` in this case) will be used.
#
# You can define any custom variable here that the notebook expects via `globals().get(...)`.
#
# ⚠️ In Jupyter, this script may be executed multiple times.
# Commenting out a variable won't reset it if it was previously defined.
# To revert to the default (e.g., via globals().get(...)), use:
#     del my_variable
# -----------------------------------------------------------------------------

my_report_identifier = "rs-dev-bge-m3"
my_config_dir = "dev_config"
my_overwrite = True
my_embeddingmodel = "BAAI/bge-m3"
#my_questions_to_process = ["16"]