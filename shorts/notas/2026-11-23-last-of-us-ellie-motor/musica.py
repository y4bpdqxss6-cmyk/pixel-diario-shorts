import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Música nueva: "sigilo" en La menor, 84 bpm: bajo pulsante en corcheas, tic de reloj (hi-hat filtrado), pad oscuro y
# una campanita aguda cada 2 compases (antes: "constructor" en Fa mayor 100 bpm con marimba y bombo suave)
def f(m): return 440*2**((m-69)/12)
beat=60/84; out=np.zeros(N)
prog=[45,41,43,40]  # Am F G Em (raíces)
pads=[[57,60,64],[53,57,60],[55,59,62],[52,55,59]]
rng=np.random.default_rng(3)
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    c=(n//8)%4; r=prog[c]
    e=min(s+int(0.3*sr),N); tt=t[s:e]-t[s]
    out[s:e]+=0.07*np.tanh(2*np.sin(2*np.pi*f(r)*tt))*np.exp(-tt*9)
    e2=min(s+int(0.04*sr),N); t2=t[s:e2]-t[s]
    ruido=rng.standard_normal(e2-s); ruido=np.diff(np.concatenate([[0],ruido]))
    out[s:e2]+=(0.025 if n%2 else 0.012)*ruido*np.exp(-t2*90)
    if n%8==0:
        e3=min(s+int(beat*4*sr),N); t3=t[s:e3]-t[s]
        for mm in pads[c]:
            out[s:e3]+=0.009*(np.sin(2*np.pi*f(mm)*t3)+0.3*np.sin(2*np.pi*f(mm)*1.003*t3))*np.minimum(1,t3*1.5)*np.exp(-t3*0.4)
    if n%32==12:
        e4=min(s+int(1.2*sr),N); t4=t[s:e4]-t[s]
        out[s:e4]+=0.02*np.sin(2*np.pi*f(88)*t4)*np.exp(-t4*3)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.5
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
