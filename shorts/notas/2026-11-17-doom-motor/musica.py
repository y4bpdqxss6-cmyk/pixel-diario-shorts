import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Mi menor, arpegio de sintetizador (onda casi cuadrada suave) + bombo + caja de ruido, 128 bpm
# (antes: marimba + bajo pulsado + clic de madera, Fa mayor 116 bpm)
bpm=128; step=60/bpm/4
prog=[[52,55,59,64],[48,52,55,60],[50,54,57,62],[47,50,54,59]]
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t); rng=np.random.default_rng(3)
n=int(dur/step)+1
for k in range(n):
    s=int(k*step*sr)
    if s>=len(t): break
    ch=prog[(k//16)%4]
    e=min(s+int(0.12*sr),len(t)); tt=t[s:e]-t[s]; fr=f(ch[k%4]+12)
    sq=np.tanh(3*np.sin(2*np.pi*fr*tt))
    out[s:e]+=0.025*sq*np.exp(-tt*18)
    if k%4==0:  # bombo
        e=min(s+int(0.25*sr),len(t)); tt=t[s:e]-t[s]
        out[s:e]+=0.16*np.sin(2*np.pi*(45+90*np.exp(-tt*30))*tt)*np.exp(-tt*9)
    if k%8==4:  # caja
        e=min(s+int(0.12*sr),len(t)); tt=t[s:e]-t[s]
        out[s:e]+=0.05*rng.standard_normal(len(tt))*np.exp(-tt*25)
    if k%16==0:  # bajo
        e=min(s+int(1.7*sr),len(t)); tt=t[s:e]-t[s]
        out[s:e]+=0.05*np.tanh(2*np.sin(2*np.pi*f(ch[0]-12)*tt))*np.exp(-tt*1.2)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.32
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
