import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Música nueva: "exploración" en Do mayor, 100 bpm: arpegio de marimba (seno con ataque corto), bombo suave en 1 y 3,
# platillo cerrado de ruido en contratiempos y pad cálido (antes: "tensión de combate" Mi menor 108 bpm, latido doble, bajo de sierra)
def f(m): return 440*2**((m-69)/12)
beat=60/100; out=np.zeros(N); rng=np.random.default_rng(3)
prog=[[60,64,67,72],[55,59,62,67],[57,60,64,69],[53,57,60,65]]  # C G Am F
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    c=(n//8)%4; nota=prog[c][[0,1,2,3,2,1,3,2][n%8]]
    e=min(s+int(0.45*sr),N); tt=t[s:e]-t[s]
    out[s:e]+=0.045*(np.sin(2*np.pi*f(nota)*tt)+0.3*np.sin(2*np.pi*f(nota)*4*tt)*np.exp(-tt*30))*np.exp(-tt*7)
    if n%4==0:
        e=min(s+int(0.3*sr),N); tt=t[s:e]-t[s]
        out[s:e]+=0.16*np.sin(2*np.pi*(50+70*np.exp(-tt*30))*tt)*np.exp(-tt*12)
    if n%2==1:
        e=min(s+int(0.05*sr),N); tt=t[s:e]-t[s]
        out[s:e]+=0.018*rng.standard_normal(e-s)*np.exp(-tt*80)
    if n%8==0:
        e=min(s+int(beat*4*sr),N); tt=t[s:e]-t[s]; r=prog[c][0]-24
        out[s:e]+=0.05*np.sin(2*np.pi*f(r)*tt)*np.exp(-tt*1.2)
for c4 in range(int(dur/(beat*4))+1):
    s=int(c4*beat*4*sr); e=min(s+int(beat*4*sr),N)
    if s>=N: break
    tt=t[s:e]-t[s]; ch=prog[c4%4]
    env=np.minimum(1,tt/0.5)*np.minimum(1,(beat*4-tt)/0.5)
    for m in ch[:3]: out[s:e]+=0.008*np.sin(2*np.pi*f(m)*tt)*env
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.5
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
