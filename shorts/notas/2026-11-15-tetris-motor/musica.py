import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
bpm=112; beat=60/bpm; step=beat/2
# Mi menor, caja de música (seno + armónico agudo) + bajo pulsante + hi-hat de ruido (antes: marimba Re dórico 100 bpm)
prog=[[52,59,64,67],[48,55,60,64],[55,62,67,71],[50,57,62,66]]
mel=[3,1,2,0,3,2,1,2]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t); rng=np.random.default_rng(4)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]
    e=min(s+int(0.9*sr),len(t)); tt=t[s:e]-t[s]
    m=ch[mel[k%8]]+12
    out[s:e]+=0.09*(np.sin(2*np.pi*f(m)*tt)+0.4*np.sin(2*np.pi*f(m)*3*tt)*np.exp(-tt*12))*np.exp(-tt*4)
    if k%2==0:
        e2=min(s+int(0.28*sr),len(t)); tt2=t[s:e2]-t[s]
        out[s:e2]+=0.13*np.tanh(3*np.sin(2*np.pi*f(ch[0]-12)*tt2))*np.exp(-tt2*8)
    e3=min(s+int(0.05*sr),len(t)); n3=e3-s
    out[s:e3]+=(0.035 if k%2 else 0.02)*rng.standard_normal(n3)*np.exp(-np.arange(n3)/sr*90)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.30
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
