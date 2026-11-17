import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Re mayor, piano suave (armónicos con caída) + colchón cálido + tic de hi-hat, 100 bpm (antes: FM + sierra Mi menor 132 bpm)
bpm=100; step=60/bpm/2
prog=[[50,57,62,66],[47,54,59,62],[43,50,55,59],[45,52,57,61]]
arp=[0,2,1,3,2,1,3,2]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t); rng=np.random.default_rng(3)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]
    e=min(s+int(0.9*sr),len(t)); tt=t[s:e]-t[s]; fr=f(ch[arp[k%8]]+12)
    out[s:e]+=0.05*(np.sin(2*np.pi*fr*tt)+0.4*np.sin(4*np.pi*fr*tt)+0.15*np.sin(6*np.pi*fr*tt))*np.exp(-tt*4)
    if k%8==0:
        e2=min(s+int(8*step*sr),len(t)); tt2=t[s:e2]-t[s]
        env=np.minimum(1,tt2/0.4)*np.minimum(1,(tt2[-1]-tt2+0.01)/0.4)
        for m in ch[:3]:
            out[s:e2]+=0.018*np.sin(2*np.pi*f(m)*tt2+0.3*np.sin(2*np.pi*0.5*tt2))*env
        e3=min(s+int(1.2*sr),len(t)); tt3=t[s:e3]-t[s]
        out[s:e3]+=0.08*np.sin(2*np.pi*f(ch[0]-12)*tt3)*np.exp(-tt3*2.5)
    if k%2==1:
        e4=min(s+int(0.04*sr),len(t)); n4=max(e4-s,0)
        out[s:e4]+=0.025*rng.standard_normal(n4)*np.exp(-np.arange(n4)/sr*120)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.35
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
