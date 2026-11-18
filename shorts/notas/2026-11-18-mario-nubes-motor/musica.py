import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Sol mayor, cuerda pulsada tipo ukulele (Karplus-Strong) + campanita + shaker suave, 104 bpm
# (antes: arpegio de sintetizador + bombo + caja, Mi menor 128 bpm)
bpm=104; step=60/bpm/2
prog=[[55,59,62,67],[52,55,59,64],[48,52,55,60],[50,54,57,62]]
def f(m): return 440*2**((m-69)/12)
rng=np.random.default_rng(11)
def pluck(fr, d=0.9):
    n=int(sr*d); p=max(2,int(sr/fr)); buf=rng.uniform(-1,1,p); out=np.zeros(n)
    for i in range(n):
        out[i]=buf[i%p]; buf[i%p]=0.996*0.5*(buf[i%p]+buf[(i+1)%p])
    return out
cache={}
out=np.zeros_like(t)
patron=[0,2,1,3,2,1,3,2]
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//8)%4]; m=ch[patron[k%8]]
    if m not in cache: cache[m]=pluck(f(m))
    a=cache[m]; e=min(s+len(a),len(t)); out[s:e]+=0.09*a[:e-s]
    if k%8==0:
        bm=ch[0]-12
        if bm not in cache: cache[bm]=pluck(f(bm),1.6)
        a=cache[bm]; e=min(s+len(a),len(t)); out[s:e]+=0.09*a[:e-s]
    if k%16==6:
        e=min(s+int(0.8*sr),len(t)); tt=t[s:e]-t[s]
        out[s:e]+=0.025*np.sin(2*np.pi*f(ch[3]+24)*tt)*np.exp(-tt*5)
    # shaker en cada corchea
    e=min(s+int(0.06*sr),len(t)); tt=t[s:e]-t[s]
    out[s:e]+=(0.018 if k%2 else 0.01)*rng.standard_normal(len(tt))*np.exp(-tt*60)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.35
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
