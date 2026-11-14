"""Honest capability registry for the RANCAGE 0.1 roadmap."""
TARGETS = [
    ("rancage-vm", "Reference bytecode VM", "implemented-experimental", "Runs RANCAGE-IR .rcb in the reference runtime"),
    ("native", "Native machine code", "planned", "x86-64, ARM64, RISC-V; platform-specific toolchains required"),
    ("wasm", "WebAssembly", "planned", "Browser and WASI-style host environments"),
    ("dotnet", ".NET", "planned", "Managed .NET integration"),
    ("jvm", "JVM", "planned", "Managed Java ecosystem integration"),
    ("javascript", "JavaScript / TypeScript", "planned", "Web and JavaScript runtimes"),
    ("lua", "Lua / Luau", "planned", "Lua hosts and Roblox Luau adapter"),
    ("kotlin", "Kotlin", "planned", "Android and Kotlin/JVM integration"),
    ("swift", "Swift", "planned", "Apple platform integration"),
    ("c", "C ABI / C source", "planned", "Native interop and embedded toolchains"),
    ("engines", "Game engine adapters", "planned", "Unity, Unreal, Godot, Roblox, and others"),
    ("embedded", "Embedded targets", "planned", "MCUs and constrained devices"),
]
