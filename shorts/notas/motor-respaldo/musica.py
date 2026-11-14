import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
bpm=132; beat=60/bpm; step=beat/4
# La menor, arpegio chiptune con onda de pulso + bajo triangular (antes: arpegio suave en Do mayor)
prog=[[57,60,64,69],[53,57,60,65],[55,59,62,67],[52,56,59,64]]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr); e=min(int((k+1)*step*sr),len(t))
    if s>=len(t): break
    ch=prog[(k//16)%4]; m=ch[k%4]+12
    tt=t[s:e]-t[s]; env=np.exp(-tt*18)
    out[s:e]+=0.10*np.sign(np.sin(2*np.pi*f(m)*tt)+0.4)*env
    if k%4==0:
        e2=min(s+int(beat*sr),len(t)); tt2=t[s:e2]-t[s]
        out[s:e2]+=0.16*(2/np.pi)*np.arcsin(np.sin(2*np.pi*f(ch[0]-12)*tt2))*np.exp(-tt2*3)
    if k%8==4:  # caja de ruido
        e3=min(s+int(0.06*sr),len(t)); out[s:e3]+=0.06*np.random.uniform(-1,1,e3-s)*np.exp(-np.arange(e3-s)/sr*50)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.35
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
