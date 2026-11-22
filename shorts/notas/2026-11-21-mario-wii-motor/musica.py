import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Chiptune alegre en Do mayor, 140 bpm: arpegio de onda cuadrada suave, bajo triangular saltarín y charles de ruido
# (antes: persecución funk en La menor 112 bpm con sirena)
def f(m): return 440*2**((m-69)/12)
beat=60/140; out=np.zeros(N); rng=np.random.default_rng(7)
acordes=[[60,64,67,72],[57,60,64,69],[53,57,60,65],[55,59,62,67]]
bajos=[36,33,29,31]
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    c=(n//8)%4
    e=min(s+int(beat/2*sr*0.8),N); tt=t[s:e]-t[s]
    fr=f(acordes[c][n%4]+12)
    out[s:e]+=0.028*np.sign(np.sin(2*np.pi*fr*tt))*np.exp(-tt*7)
    e2=min(s+int(0.03*sr),N); out[s:e2]+=0.02*rng.standard_normal(e2-s)*np.exp(-(t[s:e2]-t[s])*120)
for n in range(int(dur/beat)+2):
    s=int(n*beat*sr)
    if s>=N: break
    c=(n//4)%4; m=bajos[c]+(12 if n%2 else 0)
    e=min(s+int(beat*sr*0.85),N); tt=t[s:e]-t[s]; fr=f(m)
    tri=2*np.abs(2*((fr*tt)%1)-1)-1
    out[s:e]+=0.10*tri*np.exp(-tt*3)
    if n%2==0:
        e3=min(s+int(0.2*sr),N); t3=t[s:e3]-t[s]
        out[s:e3]+=0.15*np.sin(2*np.pi*(55+80*np.exp(-t3*30))*t3)*np.exp(-t3*12)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.45
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
