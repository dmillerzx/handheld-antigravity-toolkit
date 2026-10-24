### [Guide] How to Run Native Android Ports & Apps Directly from ES-DE (EmulationStation Desktop Edition)

### Overview
Many retro gaming handhelds running Android (such as the Retroid Pocket 5, Retroid Pocket 4 Pro, AYN Odin 2, and AYANEO Pocket S) have amazing native source ports (Super Mario 64, Apotris, Balatro, Sonic Mania Plus, AM2R, Sonic Robo Blast 2, Perfect Dark). 

By default, ES-DE's `ports` system points to RetroArch's ECWolf core. Here is how to configure ES-DE to treat native Android APK ports as games directly from your main carousel without needing third-party launcher apps.

---

### Step 1: Define Custom `ports` in `es_systems.xml`
In your ES-DE configuration directory (`/sdcard/ES-DE/custom_systems/es_systems.xml` or MicroSD `ES-DE/custom_systems/es_systems.xml`), add:

```xml
<systemList>
    <system>
        <name>ports</name>
        <fullname>Ports</fullname>
        <path>%ROMPATH%/ports</path>
        <extension>.app .APP</extension>
        <command label="Android App">%ANDROIDAPP%=%FILEINJECT%</command>
        <platform>ports</platform>
        <theme>ports</theme>
    </system>
</systemList>
```

### Step 2: Route Alternative Emulator in `es_settings.xml`
Inside `ES-DE/settings/es_settings.xml`:

```xml
<string name="AlternativeEmulator.ports" value="Android App" />
```

### Step 3: Create `.app` Pointer Files
Inside your canonical ROM folder (`ROMs/ports/`), create small plain-text files ending in `.app` containing the exact Android package name:

- `Super Mario 64.app` -> `com.izzyagamer.sm64alo`
- `Apotris.app` -> `com.apotris.android`
- `Balatro.app` -> `com.unofficial.balatro`
- `Sonic Mania Plus.app` -> `com.decomp.rsdkv5`
- `Sonic Robo Blast 2.app` -> `org.stjr.srb2`
- `Perfect Dark.app` -> `com.perfectdark.port`

When you select a game in ES-DE's Ports section, ES-DE automatically reads the package name via `%FILEINJECT%` and launches the native Android activity seamlessly!
