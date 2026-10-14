# RetroArch Audio DSP Preset - Game Boy Advance Low-Pass Filter
# Tuned to 5.5 kHz cutoff frequency to suppress Direct Sound PWM carrier noise
filters = 1
filter0 = iir

iir_type = LPF
iir_frequency = 5500.0
iir_quality = 0.707
iir_gain = 0.0
