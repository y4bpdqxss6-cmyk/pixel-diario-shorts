import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Do mayor, chiptune: arpegio de onda cuadrada + bajo triangular + hi-hat de ruido, 118 bpm
# (antes: colchón de sintetizador con trémolo + pulso grave + campana, Re menor 92 bpm)
bpm=118; beat=60/bpm; sem=beat/4
def f(m): return 440*2**((m-69)/12)
prog=[[60,64,67],[57,60,64],[53,57,60],[55,59,62]]  # C Am F G
out=np.zeros_like(t)
compas=beat*4
def sq(fr,tt,duty=0.25): return np.where((fr*tt)%1<duty,1.0,-1.0)
def tri(fr,tt): return 2*np.abs(2*((fr*tt)%1)-1)-1
n=int(dur/sem)+1
for k in range(n):
    s=int(k*sem*sr); e=min(s+int(sem*sr*0.9),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; c=int(k*sem/compas)%4
    m=prog[c][k%3]+12*((k//3)%2)
    out[s:e]+=0.025*sq(f(m),tt)*np.exp(-tt*6)
for k in range(int(dur/beat)+1):
    s=int(k*beat*sr); e=min(s+int(beat*sr*0.8),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; c=int(k*beat/compas)%4
    out[s:e]+=0.07*tri(f(prog[c][0]-24),tt)*np.exp(-tt*3)
    s2=int((k+0.5)*beat*sr); e2=min(s2+int(0.03*sr),len(t))
    if s2<len(t):
        tt2=t[s2:e2]-t[s2]
        out[s2:e2]+=0.02*np.random.default_rng(k).standard_normal(len(tt2))*np.exp(-tt2*120)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.4
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
