import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# La menor, suspenso: colchón grave con batido lento + latido doble (bombo suave) + campanita lejana, 96 bpm
# (antes: chiptune de onda cuadrada + bajo triangular + hi-hat, Do mayor 118 bpm)
bpm=96; beat=60/bpm
def f(m): return 440*2**((m-69)/12)
out=np.zeros_like(t)
prog=[45,41,43,40]  # A F G E
compas=beat*4
for c in range(int(dur/compas)+1):
    s=int(c*compas*sr); e=min(int((c+1)*compas*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]
    r=prog[c%4]
    env=np.minimum(1,(tt-tt[0])/0.3)*np.minimum(1,(tt[-1]-tt+1e-3)/0.3)
    for m,a in ((r,0.05),(r+7,0.03),(r+12,0.025),(r+15,0.015)):
        out[s:e]+=a*env*np.sin(2*np.pi*f(m)*tt)*(0.75+0.25*np.sin(2*np.pi*0.5*tt))
        out[s:e]+=a*0.5*env*np.sin(2*np.pi*f(m)*1.003*tt)
for k in range(int(dur/beat)+1):
    for off,amp in ((0,0.16),(0.22,0.10)):
        s=int((k*beat+off)*sr); e=min(s+int(0.18*sr),len(t))
        if s>=len(t) or k%2: continue
        tt=t[s:e]-t[s]
        out[s:e]+=amp*np.sin(2*np.pi*(55+60*np.exp(-tt*30))*tt)*np.exp(-tt*18)
for k in range(0,int(dur/beat)+1,6):
    s=int((k*beat+beat*0.5)*sr); e=min(s+int(1.5*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; m=[81,84,76,79][(k//6)%4]
    out[s:e]+=0.025*np.sin(2*np.pi*f(m)*tt)*np.exp(-tt*2.5)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.45
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
