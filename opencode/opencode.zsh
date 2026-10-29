# Makes `opencode` update the list of Lumen models in
# ~/.config/opencode/opencode.json before it starts, because opencode itself
# never asks Lumen which models it offers. lumen_refresh.py prints a line
# only when the list changes or cannot be updated, and opencode starts
# either way. Load it from ~/.zshrc with
#
#   source ~/repos/ai_workflow/opencode/opencode.zsh

# The script's path, found from this file's own location when it is sourced,
# so the same line works on any machine that keeps ai_workflow elsewhere.
_lumen_refresh_script="${${(%):-%x}:A:h}/lumen_refresh.py"

opencode() {
  python3 "$_lumen_refresh_script"
  command opencode "$@"
}
