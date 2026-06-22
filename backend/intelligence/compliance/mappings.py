from backend.intelligence.compliance.controls import Framework, Control

# A static catalog of framework controls we map against
CONTROLS_CATALOG = {
    # PCI DSS
    "PCI-1.2": Control(framework=Framework.PCI, id="1.2", title="Restrict connections to untrusted networks", description="Build firewall and router configurations that restrict connections between untrusted networks and any system components in the CDE."),
    "PCI-7.1": Control(framework=Framework.PCI, id="7.1", title="Limit access to system components", description="Limit access to system components and cardholder data to only those individuals whose job requires such access."),
    
    # SOC 2
    "SOC2-CC6.1": Control(framework=Framework.SOC2, id="CC6.1", title="Logical Access Security", description="The entity implements logical access security software, infrastructure, and architectures over protected information assets to protect them from security events."),
    "SOC2-CC6.6": Control(framework=Framework.SOC2, id="CC6.6", title="External Threats", description="The entity implements logical access security measures to protect against threats from sources outside its boundaries."),
    
    # NIST CSF
    "NIST-PR.AC-3": Control(framework=Framework.NIST, id="PR.AC-3", title="Remote Access is Managed", description="Remote access is managed."),
    "NIST-PR.AC-4": Control(framework=Framework.NIST, id="PR.AC-4", title="Access Permissions", description="Access permissions and authorizations are managed, incorporating the principles of least privilege and separation of duties."),
}

def map_recommendation_to_controls(rec_category: str, rec_title: str) -> list[Control]:
    """
    Given a recommendation category and title, return the Controls it maps to.
    """
    controls = []
    
    if rec_category == "EXPOSURE" and "Exposed Database" in rec_title:
        controls.extend([
            CONTROLS_CATALOG["PCI-1.2"],
            CONTROLS_CATALOG["SOC2-CC6.6"],
            CONTROLS_CATALOG["NIST-PR.AC-3"]
        ])
        
    elif rec_category == "CRITICAL_ASSET" and "Missing Ownership" in rec_title:
        controls.extend([
            CONTROLS_CATALOG["PCI-7.1"],
            CONTROLS_CATALOG["SOC2-CC6.1"]
        ])
        
    elif rec_category == "IDENTITY" and "High Risk Identity" in rec_title:
        controls.extend([
            CONTROLS_CATALOG["PCI-7.1"],
            CONTROLS_CATALOG["SOC2-CC6.1"],
            CONTROLS_CATALOG["NIST-PR.AC-4"]
        ])
        
    return controls
