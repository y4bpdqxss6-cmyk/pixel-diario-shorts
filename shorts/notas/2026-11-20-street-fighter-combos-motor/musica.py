import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Arcade de peleas en Mi menor, 128 bpm: bajo de onda cuadrada suavizada en corcheas, palmas en 2 y 4,
# bombo en cada tiempo y arpegio corto de pulso (antes: suspenso en La menor 96 bpm con colchón y latido)
bpm=128; beat=60/bpm
def f(m): return 440*2**((m-69)/12)
def sq(fr,tt): return np.tanh(4*np.sin(2*np.pi*fr*tt))
out=np.zeros_like(t)
prog=[40,36,38,35]  # E C D B
for k in range(int(dur/(beat/2))+1):
    s=int(k*beat/2*sr); e=min(s+int(beat/2*0.85*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; r=prog[(k//16)%4]+(12 if k%4==3 else 0)
    out[s:e]+=0.07*sq(f(r),tt)*np.exp(-tt*6)
for k in range(int(dur/beat)+1):
    s=int(k*beat*sr); e=min(s+int(0.16*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]
    out[s:e]+=0.17*np.sin(2*np.pi*(50+90*np.exp(-tt*35))*tt)*np.exp(-tt*16)
    if k%2==1:
        n=np.random.default_rng(k).standard_normal(e-s)
        out[s:e]+=0.05*n*np.exp(-tt*28)
for k in range(int(dur/(beat/4))+1):
    if k%8 not in (0,3,6): continue
    s=int(k*beat/4*sr); e=min(s+int(0.09*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; r=prog[(k//32)%4]+24+[0,3,7][(k//8)%3]
    out[s:e]+=0.025*sq(f(r),tt)*np.exp(-tt*25)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.4
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
