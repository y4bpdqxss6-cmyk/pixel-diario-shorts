import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Música nueva: "arcade nocturno" en La menor, 116 bpm: bajo de onda cuadrada en corcheas, pluck de onda triangular
# en semicorcheas sincopadas, palmada de ruido en 2 y 4 y bombo seco (antes: "exploración" Do mayor 100 bpm con marimba)
def f(m): return 440*2**((m-69)/12)
def sq(fr,tt): return np.sign(np.sin(2*np.pi*fr*tt))
def tri(fr,tt): return 2/np.pi*np.arcsin(np.sin(2*np.pi*fr*tt))
beat=60/116; out=np.zeros(N); rng=np.random.default_rng(7)
prog=[[57,60,64],[53,57,60],[48,52,55],[55,59,62]]  # Am F C G
patron=[1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1]
for n in range(int(dur/(beat/4))+2):
    s=int(n*beat/4*sr)
    if s>=N: break
    c=(n//16)%4; ch=prog[c]
    if patron[n%16]:
        nota=ch[(n*5)%3]+12
        e=min(s+int(0.18*sr),N); tt=t[s:e]-t[s]
        out[s:e]+=0.035*tri(f(nota),tt)*np.exp(-tt*16)
    if n%2==0:
        e=min(s+int(beat/2*0.9*sr),N); tt=t[s:e]-t[s]
        out[s:e]+=0.03*sq(f(ch[0]-24),tt)*np.exp(-tt*5)
    if n%8==0:
        e=min(s+int(0.22*sr),N); tt=t[s:e]-t[s]
        out[s:e]+=0.18*np.sin(2*np.pi*(45+90*np.exp(-tt*40))*tt)*np.exp(-tt*16)
    if n%16 in (4,12):
        e=min(s+int(0.12*sr),N); tt=t[s:e]-t[s]
        out[s:e]+=0.05*rng.standard_normal(e-s)*np.exp(-tt*35)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.45
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
