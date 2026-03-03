import { useNavigate } from "react-router-dom";
import { useBilling } from "../../hooks/useBilling";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Card } from "../../components/ui/Card";
import { Users, CheckCircle } from "lucide-react";

export default function TeamView() {
    const navigate = useNavigate();
    const { status, plan, loading: isLoading } = useBilling();
    const isSolo = plan !== "TEAM";

    if (isLoading) {
        return (
            <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0" aria-busy="true" aria-label="Loading workspace">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="space-y-2">
                        <div className="h-8 w-48 bg-slate-200 rounded animate-pulse" />
                        <div className="h-4 w-64 bg-slate-100 rounded animate-pulse" />
                    </div>
                    <div className="h-10 w-28 bg-slate-100 rounded-xl animate-pulse" />
                </div>
                <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
                    <div className="lg:col-span-2 p-0 overflow-hidden border border-slate-200 rounded-2xl animate-pulse">
                        <div className="bg-slate-50 border-b border-slate-200 px-8 py-4">
                            <div className="h-4 w-32 bg-slate-200 rounded" />
                        </div>
                        <div className="divide-y divide-slate-100">
                            {[1, 2].map((i) => (
                                <div key={i} className="px-8 py-6 flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-full bg-slate-200" />
                                        <div className="space-y-2">
                                            <div className="h-4 w-24 bg-slate-200 rounded" />
                                            <div className="h-3 w-16 bg-slate-100 rounded" />
                                        </div>
                                    </div>
                                    <div className="h-6 w-16 bg-slate-100 rounded" />
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="p-8 border border-slate-200 rounded-2xl animate-pulse">
                        <div className="h-6 w-40 bg-slate-200 rounded mb-4" />
                        <div className="space-y-4">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-4 w-full bg-slate-100 rounded" />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto space-y-6 pb-6 px-4 lg:px-0">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-slate-900 tracking-tight">Workspace</h2>
                    <p className="text-slate-500 font-medium">Collaborate and manage shared job search pipelines.</p>
                </div>
                <Button
                    variant="outline"
                    className="rounded-xl font-bold text-xs uppercase"
                    onClick={() => navigate("/app/billing")}
                >
                    {plan === "TEAM" ? "Add Seats" : "Upgrade to Team"}
                </Button>
            </div>

            <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
                <div className="lg:col-span-2">
                    <Card className="p-0 overflow-hidden border-slate-200" shadow="sm">
                        <div className="bg-slate-50 border-b border-slate-200 px-8 py-4">
                            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Active Members</p>
                        </div>
                        <div className="divide-y divide-slate-100 italic">
                            <div className="px-8 py-6 flex items-center justify-between bg-white">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white font-bold">{status?.tenant_id?.slice(0, 2).toUpperCase() || 'ME'}</div>
                                    <div>
                                        <p className="font-bold text-slate-900">You (Owner)</p>
                                        <p className="text-xs text-slate-500 font-medium">Workspace Owner</p>
                                    </div>
                                </div>
                                <Badge variant="default" className="font-bold text-[10px] uppercase">Active</Badge>
                            </div>
                            {isSolo && (
                                <div className="px-8 py-12 flex flex-col items-center justify-center text-center bg-slate-50/50">
                                    <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-300 mb-4 border border-dashed border-slate-300">
                                        <Users className="w-6 h-6" />
                                    </div>
                                    <h4 className="font-bold text-slate-900 mb-1">No teammates yet</h4>
                                    <p className="text-sm text-slate-500 max-w-xs mx-auto mb-6">Upgrade to Team to add up to 10 teammates and share your job pipeline.</p>
                                    <Button size="sm" variant="primary" onClick={() => navigate("/app/billing")} className="font-bold text-xs uppercase px-6">Upgrade to Team</Button>
                                </div>
                            )}
                        </div>
                    </Card>
                </div>

                <div className="space-y-6">
                    <Card className="p-8 border-slate-100 bg-primary-50/30" shadow="sm">
                        <h3 className="text-lg font-black text-slate-900 mb-4 font-display">Shared Features</h3>
                        <ul className="space-y-4">
                            {[
                                "Unified Job Feed",
                                "Shared Input Inbox",
                                "Collaborative Tailoring",
                                "Centralized Billing"
                            ].map(feat => (
                                <li key={feat} className="flex items-start gap-3 text-sm text-slate-600 font-medium">
                                    <div className="w-5 h-5 rounded-full bg-white flex items-center justify-center text-primary-500 shadow-sm flex-shrink-0">
                                        <CheckCircle className="w-3 h-3" />
                                    </div>
                                    {feat}
                                </li>
                            ))}
                        </ul>
                    </Card>
                </div>
            </div>
        </div>
    );
}