import numpy as np, soundfile as sf, json
sr=24000; dur=json.load(open("tiempos.json"))["dur"]
t=np.arange(int(sr*dur))/sr
# Re menor, colchón de sintetizador con trémolo + pulso grave + campana misteriosa, 92 bpm
# (antes: cuerda pulsada tipo ukulele + campanita + shaker, Sol mayor 104 bpm)
bpm=92; beat=60/bpm
def f(m): return 440*2**((m-69)/12)
prog=[[50,53,57],[46,50,53],[48,52,55],[45,49,52]]  # Dm Bb C A
out=np.zeros_like(t)
compas=beat*4
for c in range(int(dur/compas)+1):
    s=int(c*compas*sr); e=min(int((c+1)*compas*sr)+int(0.3*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; env=np.minimum(1,tt/0.4)*np.minimum(1,(e/sr-t[s]-tt)/0.3+0.0)
    env=np.clip(env,0,1)
    for m in prog[c%4]:
        fr=f(m)
        w=np.sin(2*np.pi*fr*tt)+0.5*np.sin(2*np.pi*fr*1.005*tt)+0.25*np.sin(2*np.pi*fr*2*tt)
        out[s:e]+=0.03*w*env*(0.8+0.2*np.sin(2*np.pi*5*tt))
# pulso grave en cada tiempo
for k in range(int(dur/beat)+1):
    s=int(k*beat*sr); e=min(s+int(0.35*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]; c=(int(k*beat/compas))%4
    out[s:e]+=0.12*np.sin(2*np.pi*f(prog[c][0]-12)*tt)*np.exp(-tt*9)
    if k%2==1:
        e2=min(s+int(0.05*sr),len(t)); tt2=t[s:e2]-t[s]
        out[s:e2]+=0.012*np.random.default_rng(k).standard_normal(len(tt2))*np.exp(-tt2*80)
# campana cada 2 compases
for k in range(0,int(dur/compas)+1,2):
    s=int((k*compas+beat*2.5)*sr); e=min(s+int(1.5*sr),len(t))
    if s>=len(t): break
    tt=t[s:e]-t[s]
    out[s:e]+=0.03*(np.sin(2*np.pi*f(81)*tt)+0.4*np.sin(2*np.pi*f(81)*2.76*tt))*np.exp(-tt*3)
fade=np.minimum(1,(len(t)-np.arange(len(t)))/(sr*1.0))*np.minimum(1,np.arange(len(t))/(sr*0.05))
out*=fade
voz,_=sf.read("voz.wav")
mez=voz*1.0+out[:len(voz)]*0.4
mez/=max(1,np.abs(mez).max()/0.95)
sf.write("mezcla.wav",mez,sr)
