import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Música nueva: "cuento de los años veinte" en Re mayor, 96 bpm: contrabajo pizzicato en negras, arpegio de celesta en
# corcheas y un platillo de escobilla suave (antes: "sigilo" en La menor 84 bpm con bajo pulsante y tic de reloj)
def f(m): return 440*2**((m-69)/12)
beat=60/96; out=np.zeros(N)
prog=[38,35,43,45]  # D Bm G A
arps=[[74,78,81,78],[71,74,78,74],[67,71,74,71],[69,73,76,73]]
rng=np.random.default_rng(7)
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    c=(n//8)%4; r=prog[c]
    if n%2==0:
        e=min(s+int(0.45*sr),N); tt=t[s:e]-t[s]
        nota=r if (n//2)%2==0 else r+7
        out[s:e]+=0.10*np.sin(2*np.pi*f(nota)*tt)*np.exp(-tt*7)
    e=min(s+int(0.5*sr),N); tt=t[s:e]-t[s]; m=arps[c][n%4]
    out[s:e]+=0.022*(np.sin(2*np.pi*f(m)*tt)+0.4*np.sin(2*np.pi*f(m)*2*tt))*np.exp(-tt*6)
    if n%2==1:
        e2=min(s+int(0.12*sr),N); t2=t[s:e2]-t[s]
        ruido=rng.standard_normal(e2-s); ruido=np.diff(np.concatenate([[0],ruido]))
        out[s:e2]+=0.012*ruido*np.exp(-t2*30)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.5
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
