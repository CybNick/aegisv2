import os
import re

file_path = r"d:\aegis\aegis V2\frontend\src\pages\Monitoring\index.tsx"

with open(file_path, "r", encoding="utf-8") as file:
    content = file.read()

content = content.replace("const startMutation = useAegisMutation('/monitoring/start', 'post');", "const startMutation = useMutation({ mutationFn: () => api.post('/monitoring/start') });")
content = content.replace("const stopMutation = useAegisMutation('/monitoring/stop', 'post');", "const stopMutation = useMutation({ mutationFn: () => api.post('/monitoring/stop') });")
content = content.replace("const refreshMutation = useAegisMutation('/monitoring/refresh', 'post');", "const refreshMutation = useMutation({ mutationFn: () => api.post('/monitoring/refresh') });")

# Remove unused
content = content.replace(", Cloud, ShieldAlert, CheckCircle", "")
content = content.replace("import { useMutation, useQueryClient }", "import { useMutation }")

# CyberGraph
cybergraph_path = r"d:\aegis\aegis V2\frontend\src\pages\CyberGraph\index.tsx"
with open(cybergraph_path, "r", encoding="utf-8") as file:
    cg_content = file.read()

cg_content = cg_content.replace("import { Core", "import type { Core")
cg_content = cg_content.replace("Maximize, Share2", "Maximize")

with open(cybergraph_path, "w", encoding="utf-8") as file:
    file.write(cg_content)

with open(file_path, "w", encoding="utf-8") as file:
    file.write(content)
