import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
bpm=96; beat=60/bpm; step=beat/2
# La menor, pulso de sintetizador cuadrado suave + redoble de caja militar + bombo (antes: caja de música Mi menor 112 bpm)
prog=[[45,52,57,60],[41,48,53,57],[43,50,55,59],[40,47,52,56]]
mel=[0,2,1,3,2,1,3,2]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t); rng=np.random.default_rng(4)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]
    e=min(s+int(0.9*sr),len(t)); tt=t[s:e]-t[s]
    m=ch[mel[k%8]]+12
    out[s:e]+=0.05*np.tanh(2.5*np.sin(2*np.pi*f(m)*tt))*np.exp(-tt*5)
    if k%2==0:
        e2=min(s+int(0.28*sr),len(t)); tt2=t[s:e2]-t[s]
        out[s:e2]+=0.13*np.tanh(3*np.sin(2*np.pi*f(ch[0]-12)*tt2))*np.exp(-tt2*8)
    if k%4==2:
        for r in range(3):
            s3=s+int(r*step/3*sr); e3=min(s3+int(0.07*sr),len(t)); n3=max(e3-s3,0)
            out[s3:e3]+=(0.05 if r==0 else 0.03)*rng.standard_normal(n3)*np.exp(-np.arange(n3)/sr*45)
    if k%4==0:
        e4=min(s+int(0.25*sr),len(t)); tt4=t[s:e4]-t[s]
        out[s:e4]+=0.25*np.sin(2*np.pi*(55+60*np.exp(-tt4*30))*tt4)*np.exp(-tt4*12)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.30
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
