import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
bpm=120; step=60/bpm/2
# Do mayor, marimba saltarina + bajo pizzicato + shaker (antes: pulso cuadrado La menor 96 bpm con redoble militar)
prog=[[48,55,60,64],[45,52,57,60],[41,48,53,57],[43,50,55,59]]
mel=[3,2,1,2,3,1,2,0]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t); rng=np.random.default_rng(7)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]
    e=min(s+int(0.5*sr),len(t)); tt=t[s:e]-t[s]
    m=ch[mel[k%8]]+12
    out[s:e]+=0.07*(np.sin(2*np.pi*f(m)*tt)+0.3*np.sin(2*np.pi*4*f(m)*tt)*np.exp(-tt*30))*np.exp(-tt*9)
    if k%2==0:
        e2=min(s+int(0.3*sr),len(t)); tt2=t[s:e2]-t[s]
        out[s:e2]+=0.14*np.sin(2*np.pi*f(ch[0]-12)*tt2)*np.exp(-tt2*10)
    e3=min(s+int(0.05*sr),len(t)); n3=max(e3-s,0)
    out[s:e3]+=(0.025 if k%2 else 0.04)*rng.standard_normal(n3)*np.exp(-np.arange(n3)/sr*70)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.30
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
