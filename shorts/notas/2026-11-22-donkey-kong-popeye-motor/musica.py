import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Arcade nocturno en Mi menor, 118 bpm: melodía de pulso al 25 %, bajo de diente de sierra que "rueda"
# y golpe de tambor grave en cada tiempo (antes: chiptune alegre en Do mayor 140 bpm con arpegio cuadrado)
def f(m): return 440*2**((m-69)/12)
beat=60/118; out=np.zeros(N); rng=np.random.default_rng(3)
mel=[76,79,83,79,76,74,71,74, 72,76,79,76,74,71,67,71]
bajos=[40,40,36,38]
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    e=min(s+int(beat/2*sr*0.7),N); tt=t[s:e]-t[s]
    fr=f(mel[n%16])
    ph=(fr*tt)%1
    out[s:e]+=0.022*np.where(ph<0.25,1,-0.33)*np.exp(-tt*6)
for n in range(int(dur/beat)+2):
    s=int(n*beat*sr)
    if s>=N: break
    c=(n//4)%4; m=bajos[c]+(7 if n%4==2 else 0)
    e=min(s+int(beat*sr*0.9),N); tt=t[s:e]-t[s]; fr=f(m)
    saw=2*((fr*tt)%1)-1
    out[s:e]+=0.07*saw*np.exp(-tt*2.5)
    e3=min(s+int(0.22*sr),N); t3=t[s:e3]-t[s]
    out[s:e3]+=0.16*np.sin(2*np.pi*(48+70*np.exp(-t3*25))*t3)*np.exp(-t3*10)
    if n%2==1:
        e2=min(s+int(0.08*sr),N); out[s:e2]+=0.03*rng.standard_normal(e2-s)*np.exp(-(t[s:e2]-t[s])*50)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.45
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
