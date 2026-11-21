import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(len(sf.read("voz.wav")[0]))/sr
# Ambiente de niebla en Re menor, 70 bpm: colchón grave (Re-La) que respira, caja de música dispersa y
# golpes graves suaves (antes: arcade en Mi menor 128 bpm con bajo cuadrado, bombo y palmas)
def f(m): return 440*2**((m-69)/12)
lfo=0.6+0.4*np.sin(2*np.pi*0.12*t)
out=0.06*lfo*(np.sin(2*np.pi*f(38)*t)+0.6*np.sin(2*np.pi*f(45)*t+0.3)+0.3*np.sin(2*np.pi*f(50)*t*1.002))
rng=np.random.default_rng(7)
ruido=rng.standard_normal(len(t))
# viento: ruido filtrado (media móvil) con volumen lento
k=200; viento=np.convolve(ruido,np.ones(k)/k,mode="same")*0.35*(0.5+0.5*np.sin(2*np.pi*0.07*t+1))
out+=viento
beat=60/70
mel=[74,77,81,79,77,74,73,74, 70,74,77,76,74,72,73,69]
for n in range(int(dur/(beat))+1):
    if n%2: continue
    s=int(n*beat*sr); 
    if s>=len(t): break
    e=min(s+int(1.6*sr),len(t)); tt=t[s:e]-t[s]; fr=f(mel[(n//2)%len(mel)])
    out[s:e]+=0.045*(np.sin(2*np.pi*fr*tt)+0.3*np.sin(2*np.pi*fr*2*tt)+0.12*np.sin(2*np.pi*fr*3.01*tt))*np.exp(-tt*3)
for n in range(int(dur/(beat*4))+1):
    s=int(n*beat*4*sr)
    if s>=len(t): break
    e=min(s+int(1.2*sr),len(t)); tt=t[s:e]-t[s]
    out[s:e]+=0.14*np.sin(2*np.pi*(38+30*np.exp(-tt*8))*tt)*np.exp(-tt*3.5)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.45
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
