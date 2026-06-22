import os

files_to_fix = [
    "src/hooks/useMode.tsx",
    "src/pages/AlertCenter/index.tsx",
    "src/pages/Connectors/Wizard.tsx",
    "src/pages/CyberGraph/index.tsx",
    "src/pages/Home/index.tsx",
    "src/pages/Monitoring/index.tsx",
    "src/pages/ScanCenter/index.tsx",
    "src/pages/ScanResults/index.tsx"
]

for f in files_to_fix:
    path = os.path.join(r"d:\aegis\aegis V2\frontend", f)
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as file:
        content = file.read()
        
    # Hacky fixes for the specific errors
    if f == "src/hooks/useMode.tsx":
        content = content.replace("import { useState, useEffect }", "import { useState }")
    if f == "src/pages/AlertCenter/index.tsx":
        content = content.replace("import React, { useState }", "import { useState }")
        content = content.replace("AlertTriangle, Filter", "AlertTriangle")
    if f == "src/pages/Connectors/Wizard.tsx":
        content = content.replace("import React, { useState }", "import { useState }")
    if f == "src/pages/CyberGraph/index.tsx":
        content = content.replace("import { Core, SingularElementReturnValue }", "import type { Core, SingularElementReturnValue }")
        content = content.replace("Maximize, Share2", "Maximize")
    if f == "src/pages/Home/index.tsx":
        content = content.replace("import React from 'react';\n", "")
        content = content.replace("CheckCircle, Search, LayoutDashboard, Cloud", "CheckCircle, Cloud")
    if f == "src/pages/Monitoring/index.tsx":
        content = content.replace("import React, { useState }", "import { useState }")
        content = content.replace("Activity, Settings, Play, Square, Cloud, ShieldAlert, CheckCircle", "Activity, Settings, Play, Square")
        content = content.replace("useAegisQuery, useAegisMutation", "useAegisQuery")
    if f == "src/pages/ScanCenter/index.tsx":
        content = content.replace("import React, { useState }", "import { useState }")
        content = content.replace("const [isValidated, setIsValidated] = useState(false);", "")
    if f == "src/pages/ScanResults/index.tsx":
        content = content.replace("import React, { useState, useEffect }", "import React, { useState }")
        content = content.replace("import React, { useState }", "import { useState }")

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

print("Fixed TS errors")
