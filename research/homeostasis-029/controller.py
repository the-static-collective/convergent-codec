"""Causal repair governor. No access to hidden outage events or future material."""
class Governor:
    def __init__(self,kind,budget,horizon):
        self.kind=kind;self.budget=budget;self.horizon=horizon
        self.mode='durable';self.risk=0.;self.paired=0.;self.last_wipes=0;self.last_switch=-4
    def step(self,t,online,wipes,spent):
        new=max(0,sum(wipes)-self.last_wipes);self.last_wipes=sum(wipes)
        self.risk=.85*self.risk+.15*min(1,new/2)
        self.paired=.85*self.paired+.15*(sum(not ({i,i+1}&online) for i in (0,2,4))/3)
        remain=max(0,self.budget-spent)
        regular=max(0,min(6500,remain,int(self.budget*(.25+.75*(t+1)/self.horizon))-spent))
        if self.kind=='paced':return 'reactive',regular,regular
        if t-self.last_switch>=4:
            next_mode=self.mode
            if self.paired>.20:next_mode='durable'
            elif self.risk>.08:next_mode='adaptive'
            elif self.paired<.12 and self.risk<.035:next_mode='reactive'
            if next_mode!=self.mode:self.mode=next_mode;self.last_switch=t
        if self.kind=='switch':return self.mode,min(6500,remain),min(6500,remain)
        emergency=min(6500,remain,regular+int(.12*remain)) if new else regular
        if self.kind=='reserve':return 'reactive',regular,emergency
        return self.mode,regular,emergency
