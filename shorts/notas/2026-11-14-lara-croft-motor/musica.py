import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
bpm=100; beat=60/bpm; step=beat/2
# Re dórico, marimba de seno con decaimiento + tambor grave de aventura (antes: chiptune La menor 132 bpm)
prog=[[50,57,62,65],[48,55,60,64],[53,57,60,65],[50,57,62,69]]
mel=[0,2,1,3,2,1,0,1]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr); e=min(s+int(0.6*sr),len(t))
    if s>=len(t): break
    ch=prog[(k//8)%4]; m=ch[mel[k%8]]+12
    tt=t[s:e]-t[s]; env=np.exp(-tt*7)
    out[s:e]+=0.12*(np.sin(2*np.pi*f(m)*tt)+0.3*np.sin(2*np.pi*f(m)*4*tt)*np.exp(-tt*25))*env
    if k%4==0:
        e2=min(s+int(0.35*sr),len(t)); tt2=t[s:e2]-t[s]
        fr=90*np.exp(-tt2*12)+45
        out[s:e2]+=0.22*np.sin(2*np.pi*np.cumsum(fr)/sr)*np.exp(-tt2*9)
    if k%8==0:
        e3=min(s+int(2*beat*sr),len(t)); tt3=t[s:e3]-t[s]
        out[s:e3]+=0.07*np.sin(2*np.pi*f(ch[0]-12)*tt3)*np.exp(-tt3*1.2)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.33
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
