import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
voz,_=sf.read("voz.wav"); N=len(voz)
t=np.arange(N)/sr
# Música nueva: "constructor" en Fa mayor, 100 bpm: arpegio de marimba en corcheas, bombo suave y pad cálido
# (antes: noir en Re menor 88 bpm con contrabajo caminante, escobillas y vibráfono)
def f(m): return 440*2**((m-69)/12)
beat=60/100; out=np.zeros(N)
prog=[[53,57,60,64],[50,53,57,60],[46,50,53,57],[48,52,55,58]]  # Fmaj7 Dm7 Bbmaj7 C7
patron=[0,2,1,3,2,1,3,2]
for n in range(int(dur/(beat/2))+2):
    s=int(n*beat/2*sr)
    if s>=N: break
    c=prog[(n//8)%4]; m=c[patron[n%8]]+12
    e=min(s+int(0.5*sr),N); tt=t[s:e]-t[s]
    out[s:e]+=0.05*(np.sin(2*np.pi*f(m)*tt)+0.35*np.sin(2*np.pi*f(m)*4*tt)*np.exp(-tt*30))*np.exp(-tt*7)
    if n%2==0:  # bombo suave en cada tiempo
        e2=min(s+int(0.2*sr),N); t2=t[s:e2]-t[s]
        out[s:e2]+=(0.09 if (n//2)%2==0 else 0.05)*np.sin(2*np.pi*(55+70*np.exp(-t2*30))*t2)*np.exp(-t2*16)
    if n%8==0:
        e3=min(s+int(beat*4*sr),N); t3=t[s:e3]-t[s]
        for mm in c:
            out[s:e3]+=0.010*np.sin(2*np.pi*f(mm)*t3)*np.minimum(1,t3*4)*np.exp(-t3*0.5)
fade=np.minimum(1,(N-np.arange(N))/(sr*1.0))*np.minimum(1,np.arange(N)/(sr*0.03))
out*=fade
mez=voz*1.0+out*0.5
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
