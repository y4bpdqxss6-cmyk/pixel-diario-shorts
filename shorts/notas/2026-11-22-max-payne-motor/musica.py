import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Noir en Re menor, 88 bpm: contrabajo caminante (onda triangular), escobillas de ruido y acordes de vibráfono
# (antes: arcade nocturno en Mi menor 118 bpm con pulso y bajo de sierra)
def f(m): return 440*2**((m-69)/12)
beat=60/88; out=np.zeros(N); rng=np.random.default_rng(7)
walk=[38,41,43,45, 46,45,43,41, 36,40,43,45, 37,40,43,45]
acordes=[[62,65,69,72],[58,62,65,69],[60,64,67,70],[57,61,64,67]]
for n in range(int(dur/beat)+2):
    s=int(n*beat*sr)
    if s>=N: break
    e=min(s+int(beat*sr*0.95),N); tt=t[s:e]-t[s]; fr=f(walk[n%16])
    tri=2*np.abs(2*((fr*tt)%1)-1)-1
    out[s:e]+=0.11*tri*np.exp(-tt*3)
    # escobilla en cada tiempo, acento en 2 y 4
    e2=min(s+int(0.18*sr),N); t2=t[s:e2]-t[s]
    out[s:e2]+=(0.035 if n%2 else 0.018)*rng.standard_normal(e2-s)*np.exp(-t2*18)
    if n%4==0:
        c=acordes[(n//4)%4]; e3=min(s+int(beat*4*sr),N); t3=t[s:e3]-t[s]
        for m in c:
            out[s:e3]+=0.012*np.sin(2*np.pi*f(m)*t3)*(1+0.3*np.sin(2*np.pi*5*t3))*np.exp(-t3*0.9)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.5
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
