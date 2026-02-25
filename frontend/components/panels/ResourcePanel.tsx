"use client";

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Loader2 } from 'lucide-react';

export interface ForceUnit {
    id: string;
    branch: string;
    unit_type?: string;
    location?: string;
    status?: string;
    role?: string;
    readiness_turns?: number;
    notes?: string;
}

export interface StockpileItem {
    category: string;
    name: string;
    count: number;
    note?: string;
}

export interface ResourceData {
    forces: ForceUnit[];
    stockpiles: StockpileItem[];
}

interface ResourcePanelProps {
    isOpen: boolean;
    onClose: (open: boolean) => void;
    resources: ResourceData | null;
}

export function ResourcePanel({ isOpen, onClose, resources }: ResourcePanelProps) {
    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl bg-slate-950 border-slate-800 max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>UK MILITARY RESOURCES</DialogTitle>
                    <DialogDescription>Current forces and ammunition stockpiles available for deployment.</DialogDescription>
                </DialogHeader>
                {resources ? (
                    <Tabs defaultValue="forces">
                        <TabsList className="bg-slate-900 border border-slate-800">
                            <TabsTrigger value="forces">Military Forces</TabsTrigger>
                            <TabsTrigger value="stockpiles">Stockpiles</TabsTrigger>
                        </TabsList>
                        <TabsContent value="forces" className="mt-4">
                            {resources.forces && resources.forces.length > 0 ? (
                                <div className="space-y-4">
                                    {/* Naval Forces */}
                                    {resources.forces.filter(f => f.branch === 'naval').length > 0 && (
                                        <Card className="bg-slate-900 border-slate-800">
                                            <CardHeader><CardTitle className="text-sm">Naval Assets</CardTitle></CardHeader>
                                            <CardContent>
                                                <Table>
                                                    <TableHeader><TableRow><TableHead>Unit</TableHead><TableHead>Type</TableHead><TableHead>Location</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                                                    <TableBody>
                                                        {resources.forces.filter(f => f.branch === 'naval').map((u, i) => (
                                                            <TableRow key={i}>
                                                                <TableCell className="font-bold text-xs">{u.id}</TableCell>
                                                                <TableCell className="text-xs text-slate-400">{u.unit_type || '—'}</TableCell>
                                                                <TableCell className="text-xs text-slate-400">{u.location || '—'}</TableCell>
                                                                <TableCell className="text-xs text-muted-foreground">{u.status || '—'}</TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </CardContent>
                                        </Card>
                                    )}
                                    {/* Air Forces */}
                                    {resources.forces.filter(f => f.branch === 'air').length > 0 && (
                                        <Card className="bg-slate-900 border-slate-800">
                                            <CardHeader><CardTitle className="text-sm">Air Assets</CardTitle></CardHeader>
                                            <CardContent>
                                                <Table>
                                                    <TableHeader><TableRow><TableHead>Unit</TableHead><TableHead>Type</TableHead><TableHead>Location</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                                                    <TableBody>
                                                        {resources.forces.filter(f => f.branch === 'air').map((u, i) => (
                                                            <TableRow key={i}>
                                                                <TableCell className="font-bold text-xs">{u.id}</TableCell>
                                                                <TableCell className="text-xs text-slate-400">{u.unit_type || '—'}</TableCell>
                                                                <TableCell className="text-xs text-slate-400">{u.location || '—'}</TableCell>
                                                                <TableCell className="text-xs text-muted-foreground">{u.status || '—'}</TableCell>
                                                            </TableRow>
                                                        ))}
                                                    </TableBody>
                                                </Table>
                                            </CardContent>
                                        </Card>
                                    )}
                                </div>
                            ) : (
                                <div className="text-center py-8 text-slate-500 text-sm">No force data available</div>
                            )}
                        </TabsContent>
                        <TabsContent value="stockpiles" className="mt-4">
                            {resources.stockpiles && resources.stockpiles.length > 0 ? (
                                <Card className="bg-slate-900 border-slate-800">
                                    <CardContent className="pt-6">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead>Category</TableHead>
                                                    <TableHead>Item</TableHead>
                                                    <TableHead className="text-right">Count</TableHead>
                                                    <TableHead>Notes</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {resources.stockpiles.map((item, i) => (
                                                    <TableRow key={i}>
                                                        <TableCell className="text-xs text-slate-500 capitalize">{item.category.replace(/_/g, ' ')}</TableCell>
                                                        <TableCell className="text-xs font-medium text-slate-300">{item.name.replace(/_/g, ' ')}</TableCell>
                                                        <TableCell className="text-xs font-bold text-right text-blue-400">{item.count}</TableCell>
                                                        <TableCell className="text-xs text-slate-500 max-w-xs truncate">{item.note || '—'}</TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </CardContent>
                                </Card>
                            ) : (
                                <div className="text-center py-8 text-slate-500 text-sm">No stockpile data available</div>
                            )}
                        </TabsContent>
                    </Tabs>
                ) : <Loader2 className="animate-spin mx-auto" />}
            </DialogContent>
        </Dialog>
    );
}

