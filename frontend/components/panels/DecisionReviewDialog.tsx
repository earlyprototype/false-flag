import React from 'react';
import { AlertTriangle, Check, X, Edit, ShieldAlert, FileText, Clock, Users } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

export interface CriticalConcern {
    role: string;
    concern: string;
    recommendation: string;
}

export interface InterpretationData {
    interpretation: string;
    critical_concerns: CriticalConcern[];
    forces_involved?: string[];
    timeline?: string;
}

interface DecisionReviewDialogProps {
    isOpen: boolean;
    onClose: () => void;
    decisionText: string;
    interpretation: InterpretationData | null;
    onApplyRecommendations: () => void;
    onModify: () => void;
    onIgnoreAndProceed: () => void;
    onReturnToDiscussion: () => void;
    isProcessing: boolean;
}

export function DecisionReviewDialog({
    isOpen,
    onClose,
    decisionText,
    interpretation,
    onApplyRecommendations,
    onModify,
    onIgnoreAndProceed,
    onReturnToDiscussion,
    isProcessing
}: DecisionReviewDialogProps) {
    if (!interpretation) return null;

    const hasConcerns = interpretation.critical_concerns && interpretation.critical_concerns.length > 0;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-3xl bg-slate-950 border-slate-800 max-h-[90vh] overflow-hidden flex flex-col p-0 gap-0">
                <DialogHeader className="p-6 pb-2 bg-slate-900/50 border-b border-slate-800">
                    <DialogTitle className="text-xl font-black tracking-tight text-white flex items-center gap-2">
                        <ShieldAlert className="text-yellow-500 h-6 w-6" />
                        DECISION REVIEW
                    </DialogTitle>
                    <DialogDescription className="font-mono text-xs text-slate-400 uppercase tracking-wider">
                        Strategic Assessment & Advisory Pushback
                    </DialogDescription>
                </DialogHeader>

                <ScrollArea className="flex-1 p-6">
                    <div className="space-y-6">
                        {/* SECTION 1: YOUR DECISION */}
                        <div className="space-y-2">
                            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Proposed Action</h3>
                            <div className="p-4 bg-black/40 border border-slate-800 rounded text-slate-200 font-serif text-lg italic leading-relaxed">
                                "{decisionText}"
                            </div>
                        </div>

                        {/* SECTION 2: INTERPRETATION */}
                        <div className="space-y-2">
                            <h3 className="text-xs font-bold text-blue-500 uppercase tracking-widest flex items-center gap-2">
                                <FileText className="h-3 w-3" /> Operational Interpretation
                            </h3>
                            <Card className="bg-slate-900/50 border-slate-800">
                                <CardContent className="p-4 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                                    {interpretation.interpretation}
                                </CardContent>
                            </Card>
                            
                            {/* Metadata chips (mocked for now if not in API yet) */}
                            <div className="flex gap-2">
                                <Badge variant="outline" className="bg-slate-900 text-slate-400 border-slate-700 flex gap-1">
                                    <Clock className="h-3 w-3" /> {interpretation.timeline || "Immediate"}
                                </Badge>
                                <Badge variant="outline" className="bg-slate-900 text-slate-400 border-slate-700 flex gap-1">
                                    <Users className="h-3 w-3" /> {interpretation.forces_involved?.length || 0} Assets
                                </Badge>
                            </div>
                        </div>

                        {/* SECTION 3: CRITICAL CONCERNS */}
                        <div className="space-y-2">
                            <h3 className="text-xs font-bold text-red-500 uppercase tracking-widest flex items-center gap-2">
                                <AlertTriangle className="h-3 w-3" /> Critical Advisory
                            </h3>
                            
                            {hasConcerns ? (
                                <div className="space-y-3">
                                    {interpretation.critical_concerns.map((c, idx) => (
                                        <Alert key={idx} className="bg-red-950/10 border-red-900/30">
                                            <AlertTriangle className="h-4 w-4 text-red-500" />
                                            <AlertTitle className="text-red-400 font-bold text-xs uppercase mb-1">
                                                {c.role}
                                            </AlertTitle>
                                            <AlertDescription className="text-slate-300 text-sm space-y-2">
                                                <p>{c.concern}</p>
                                                <div className="flex items-start gap-2 text-green-400 bg-green-950/10 p-2 rounded text-xs">
                                                    <Check className="h-3 w-3 mt-0.5 shrink-0" />
                                                    <span className="font-bold">Recommendation: {c.recommendation}</span>
                                                </div>
                                            </AlertDescription>
                                        </Alert>
                                    ))}
                                </div>
                            ) : (
                                <Alert className="bg-green-950/10 border-green-900/30">
                                    <Check className="h-4 w-4 text-green-500" />
                                    <AlertTitle className="text-green-400 font-bold text-xs uppercase">No Objections</AlertTitle>
                                    <AlertDescription className="text-slate-400 text-xs">
                                        Advisors have raised no critical concerns with this course of action.
                                    </AlertDescription>
                                </Alert>
                            )}
                        </div>
                    </div>
                </ScrollArea>

                <div className="p-4 bg-slate-900/80 border-t border-slate-800 backdrop-blur">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                        {hasConcerns && (
                            <Button 
                                variant="outline" 
                                className="border-green-900/50 text-green-400 hover:bg-green-950/30 hover:text-green-300 h-auto py-3 flex flex-col items-start gap-1"
                                onClick={onApplyRecommendations}
                                disabled={isProcessing}
                            >
                                <span className="text-xs font-bold flex items-center gap-2 uppercase">
                                    <Check className="h-3 w-3" /> Apply Recommendations
                                </span>
                                <span className="text-[10px] text-slate-500 font-normal">Auto-amend decision text</span>
                            </Button>
                        )}
                        
                        <Button 
                            variant="outline" 
                            className="border-blue-900/50 text-blue-400 hover:bg-blue-950/30 hover:text-blue-300 h-auto py-3 flex flex-col items-start gap-1"
                            onClick={onModify}
                            disabled={isProcessing}
                        >
                            <span className="text-xs font-bold flex items-center gap-2 uppercase">
                                <Edit className="h-3 w-3" /> Modify Manually
                            </span>
                            <span className="text-[10px] text-slate-500 font-normal">Edit text and resubmit</span>
                        </Button>
                    </div>

                    <div className="flex justify-between items-center pt-2 border-t border-slate-800/50">
                        <Button 
                            variant="ghost" 
                            className="text-slate-500 hover:text-slate-300 text-xs"
                            onClick={onReturnToDiscussion}
                            disabled={isProcessing}
                        >
                            <X className="mr-2 h-3 w-3" /> Return to Discussion
                        </Button>

                        <Button 
                            variant="destructive" 
                            className="font-bold bg-red-600 hover:bg-red-700 text-white shadow-[0_0_15px_rgba(220,38,38,0.5)]"
                            onClick={onIgnoreAndProceed}
                            disabled={isProcessing}
                        >
                            {hasConcerns ? "IGNORE & EXECUTE" : "CONFIRM & EXECUTE"}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

