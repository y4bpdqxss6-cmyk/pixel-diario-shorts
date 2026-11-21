import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Persecución funk en La menor, 112 bpm: bajo sintético con slap, charles constante, bombo/caja y un "uiu" de sirena
# muy suave cada 4 compases (antes: ambiente de niebla en Re menor 70 bpm con caja de música)
def f(m): return 440*2**((m-69)/12)
beat=60/112; out=np.zeros(N); rng=np.random.default_rng(3)
bajo=[45,45,57,45,48,50,52,55, 45,45,57,45,43,43,55,47]
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    e=min(s+int(beat/2*sr*0.9),N); tt=t[s:e]-t[s]; fr=f(bajo[n%len(bajo)]-12)
    w=np.sign(np.sin(2*np.pi*fr*tt))*0.5+np.sin(2*np.pi*fr*tt)
    out[s:e]+=0.07*w*np.exp(-tt*6)
    # charles
    e2=min(s+int(0.04*sr),N); out[s:e2]+=0.035*rng.standard_normal(e2-s)*np.exp(-(t[s:e2]-t[s])*90)
for n in range(int(dur/beat)+2):
    s=int(n*beat*sr)
    if s>=N: break
    e=min(s+int(0.3*sr),N); tt=t[s:e]-t[s]
    if n%2==0: out[s:e]+=0.22*np.sin(2*np.pi*(50+90*np.exp(-tt*25))*tt)*np.exp(-tt*9)
    else:
        e2=min(s+int(0.15*sr),N); out[s:e2]+=0.08*rng.standard_normal(e2-s)*np.exp(-(t[s:e2]-t[s])*25)
for n in range(0,int(dur/(beat*16))+1):
    s=int((n*16+12)*beat*sr)
    if s>=N: break
    e=min(s+int(2*sr),N); tt=t[s:e]-t[s]
    fr=700+250*np.sign(np.sin(2*np.pi*1.5*tt))
    out[s:e]+=0.025*np.sin(2*np.pi*np.cumsum(fr)/sr)*np.minimum(1,tt*4)*np.minimum(1,(2-tt)*4)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.42
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
