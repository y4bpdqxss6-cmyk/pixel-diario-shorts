import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Mi menor, sintetizador tipo FM brillante + bajo de sierra + caja electrónica, 132 bpm (antes: marimba + pizzicato Do mayor 120 bpm)
bpm=132; step=60/bpm/2
prog=[[40,47,52,55],[36,43,48,52],[38,45,50,54],[35,42,47,50]]
mel=[2,3,1,3,2,0,3,1]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t); rng=np.random.default_rng(11)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]
    e=min(s+int(0.35*sr),len(t)); tt=t[s:e]-t[s]
    m=ch[mel[k%8]]+24; fr=f(m)
    out[s:e]+=0.06*np.sin(2*np.pi*fr*tt+2.2*np.exp(-tt*12)*np.sin(2*np.pi*2*fr*tt))*np.exp(-tt*7)
    if k%2==0:
        e2=min(s+int(0.25*sr),len(t)); tt2=t[s:e2]-t[s]; fb=f(ch[0])
        saw=2*((tt2*fb)%1)-1
        out[s:e2]+=0.07*saw*np.exp(-tt2*8)
    if k%4==2:
        e3=min(s+int(0.12*sr),len(t)); n3=max(e3-s,0)
        out[s:e3]+=0.08*rng.standard_normal(n3)*np.exp(-np.arange(n3)/sr*30)
    if k%4==0:
        e4=min(s+int(0.15*sr),len(t)); tt4=t[s:e4]-t[s]
        out[s:e4]+=0.18*np.sin(2*np.pi*(55+90*np.exp(-tt4*30))*tt4)*np.exp(-tt4*20)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.28
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
