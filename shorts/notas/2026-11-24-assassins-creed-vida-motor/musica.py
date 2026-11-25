import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Música nueva: "tensión de combate" en Mi menor, 108 bpm: latido doble (bombo grave tipo corazón), bajo de sierra
# suavizado en corcheas y un pad de cuerdas oscuro (antes: "cuento años veinte" Re mayor 96 bpm con contrabajo y celesta)
def f(m): return 440*2**((m-69)/12)
beat=60/108; out=np.zeros(N)
prog=[40,36,38,35]  # Em C D B
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    c=(n//8)%4; r=prog[c]
    # bajo en corcheas (sierra suavizada)
    e=min(s+int(0.2*sr),N); tt=t[s:e]-t[s]
    ph=(f(r)*tt)%1.0
    out[s:e]+=0.05*(2*ph-1)*np.exp(-tt*10)
    # latido: tum-tum en el tiempo 1 y su eco
    if n%4==0 or n%4==1:
        e=min(s+int(0.25*sr),N); tt=t[s:e]-t[s]
        amp=0.20 if n%4==0 else 0.12
        out[s:e]+=amp*np.sin(2*np.pi*(55+60*np.exp(-tt*25))*tt)*np.exp(-tt*14)
# pad
for c4 in range(int(dur/(beat*4))+1):
    s=int(c4*beat*4*sr); e=min(s+int(beat*4*sr),N)
    if s>=N: break
    tt=t[s:e]-t[s]; r=prog[c4%4]+24
    env=np.minimum(1,tt/0.4)*np.minimum(1,(beat*4-tt)/0.4)
    for m in (r, r+7, r+12): out[s:e]+=0.012*np.sin(2*np.pi*f(m)*tt+0.3*np.sin(2*np.pi*5*tt))*env
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.5
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
