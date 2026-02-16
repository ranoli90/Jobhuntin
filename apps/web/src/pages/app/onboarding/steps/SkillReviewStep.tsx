import * as React from "react";
import { Star, Edit2, Trash2, Plus, Check, X, AlertCircle, Sparkles, ArrowLeft, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../../../../components/ui/Button";
import { Input } from "../../../../components/ui/Input";
import { LoadingSpinner } from "../../../../components/ui/LoadingSpinner";
import { RichSkill } from "../../../../types/onboarding";

interface SkillReviewStepProps {
    onNext: () => void;
    onPrev: () => void;
    richSkills: RichSkill[];
    setRichSkills: React.Dispatch<React.SetStateAction<RichSkill[]>>;
    isSaving: boolean;
}

function getConfidenceLevel(confidence: number): { label: string; color: string; bgColor: string } {
    if (confidence >= 0.8) {
        return { label: "HIGH", color: "text-emerald-600", bgColor: "bg-emerald-100" };
    } else if (confidence >= 0.5) {
        return { label: "MEDIUM", color: "text-amber-600", bgColor: "bg-amber-100" };
    } else {
        return { label: "LOW", color: "text-slate-600", bgColor: "bg-slate-100" };
    }
}

function ConfidenceBadge({ confidence }: { confidence: number }) {
    const { label, color, bgColor } = getConfidenceLevel(confidence);
    return (
        <span className={`px-1.5 md:px-2 py-0.5 text-[8px] md:text-[10px] font-black rounded-full ${bgColor} ${color}`}>
            {label}
        </span>
    );
}

interface SkillRowProps {
    skill: RichSkill;
    onEdit: () => void;
    onDelete: () => void;
}

function SkillRow({ skill, onEdit, onDelete }: SkillRowProps) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="flex items-center gap-2 md:gap-3 p-2.5 md:p-3 rounded-xl bg-white border border-slate-100 hover:border-slate-200 hover:shadow-sm transition-all group"
        >
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 md:gap-2 flex-wrap">
                    <span className="font-semibold text-slate-900 text-xs md:text-sm truncate">{skill.skill}</span>
                    <ConfidenceBadge confidence={skill.confidence} />
                    {skill.verified && (
                        <span className="px-1.5 py-0.5 text-[8px] font-bold rounded-full bg-blue-50 text-blue-600 border border-blue-100">VERIFIED</span>
                    )}
                </div>
                <div className="flex flex-wrap gap-x-2 md:gap-x-3 gap-y-0.5 text-[10px] md:text-xs text-slate-500 mt-0.5 md:mt-1">
                    {skill.years_actual && (
                        <span className="flex items-center gap-0.5">
                            <Star className="w-2.5 h-2.5 md:w-3 md:h-3 text-amber-400" />
                            {skill.years_actual} yrs
                        </span>
                    )}
                    {skill.project_count > 0 && (
                        <span>{skill.project_count} projects</span>
                    )}
                </div>
            </div>
            <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                <button
                    onClick={onEdit}
                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                    aria-label="Edit skill"
                >
                    <Edit2 className="w-3.5 h-3.5 md:w-4 md:h-4" />
                </button>
                <button
                    onClick={onDelete}
                    className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition-colors"
                    aria-label="Delete skill"
                >
                    <Trash2 className="w-3.5 h-3.5 md:w-4 md:h-4" />
                </button>
            </div>
        </motion.div>
    );
}

interface AddSkillFormProps {
    onAdd: (skill: RichSkill) => void;
    onCancel: () => void;
}

function AddSkillForm({ onAdd, onCancel }: AddSkillFormProps) {
    const [skillName, setSkillName] = React.useState("");
    const [years, setYears] = React.useState("");
    const [context, setContext] = React.useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!skillName.trim()) return;

        const newSkill: RichSkill = {
            skill: skillName.trim(),
            confidence: 0.5,
            years_actual: years ? parseFloat(years) : null,
            context: context.trim(),
            last_used: null,
            verified: false,
            related_to: [],
            source: "manual",
            project_count: 0,
        };

        onAdd(newSkill);
        setSkillName("");
        setYears("");
        setContext("");
    };

    return (
        <motion.form
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            onSubmit={handleSubmit}
            className="p-3 md:p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-3"
        >
            <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-emerald-600" />
                <span className="font-bold text-emerald-800 text-sm">Add a Skill</span>
            </div>
            <div className="grid gap-2 md:grid-cols-3">
                <Input
                    type="text"
                    placeholder="Skill name"
                    value={skillName}
                    onChange={(e) => setSkillName(e.target.value)}
                    className="bg-white text-sm"
                />
                <Input
                    type="number"
                    placeholder="Years"
                    value={years}
                    onChange={(e) => setYears(e.target.value)}
                    className="bg-white text-sm"
                    min="0"
                    max="50"
                    step="0.5"
                />
                <Input
                    type="text"
                    placeholder="Context (optional)"
                    value={context}
                    onChange={(e) => setContext(e.target.value)}
                    className="bg-white text-sm"
                />
            </div>
            <div className="flex justify-end gap-2">
                <Button type="button" variant="ghost" onClick={onCancel} className="h-8 text-xs">
                    <X className="w-3 h-3 mr-1" />
                    Cancel
                </Button>
                <Button type="submit" disabled={!skillName.trim()} className="h-8 text-xs bg-emerald-600 hover:bg-emerald-500">
                    <Check className="w-3 h-3 mr-1" />
                    Add Skill
                </Button>
            </div>
        </motion.form>
    );
}

export function SkillReviewStep({
    onNext,
    onPrev,
    richSkills,
    setRichSkills,
    isSaving,
}: SkillReviewStepProps) {
    const [isAddingSkill, setIsAddingSkill] = React.useState(false);
    const [editingIndex, setEditingIndex] = React.useState<number | null>(null);

    const highSkills = richSkills.filter(s => s.confidence >= 0.8);
    const mediumSkills = richSkills.filter(s => s.confidence >= 0.5 && s.confidence < 0.8);
    const lowSkills = richSkills.filter(s => s.confidence < 0.5);

    const handleAddSkill = (skill: RichSkill) => {
        const normalizedSkillName = skill.skill.toLowerCase().trim();
        const isDuplicate = richSkills.some(
            s => s.skill.toLowerCase().trim() === normalizedSkillName
        );
        if (isDuplicate) {
            return;
        }
        setRichSkills(prev => [...prev, skill]);
        setIsAddingSkill(false);
    };

    const handleDeleteSkill = (index: number) => {
        setRichSkills(prev => prev.filter((_, i) => i !== index));
    };

    const handleUpdateSkill = (index: number, updates: Partial<RichSkill>) => {
        setRichSkills(prev => prev.map((s, i) => i === index ? { ...s, ...updates } : s));
        setEditingIndex(null);
    };

    return (
        <div>
            <div className="mb-4 md:mb-6 flex items-center gap-3 md:gap-4 border-b border-slate-100 pb-4 md:pb-6">
                <div className="flex h-10 w-12 md:h-12 md:w-14 shrink-0 items-center justify-center rounded-xl md:rounded-2xl bg-emerald-50 border border-emerald-100 text-emerald-600 shadow-sm">
                    <Sparkles className="h-5 w-5 md:h-6 md:w-6" />
                </div>
                <div className="min-w-0">
                    <h2 className="font-display text-lg md:text-2xl font-bold text-slate-900 tracking-tight">Review Your Skills</h2>
                    <p className="text-xs md:text-sm text-slate-500 font-medium">{richSkills.length} skills detected from your resume</p>
                </div>
            </div>

            {richSkills.length === 0 ? (
                <div className="text-center py-8 md:py-12">
                    <div className="w-14 h-14 md:w-16 md:h-16 rounded-2xl bg-slate-100 mx-auto mb-4 flex items-center justify-center">
                        <AlertCircle className="w-6 h-6 md:w-7 md:h-7 text-slate-400" />
                    </div>
                    <p className="text-slate-600 text-sm font-medium mb-1">No skills detected</p>
                    <p className="text-slate-400 text-xs mb-4">Add your skills manually to improve job matching</p>
                    <Button
                        onClick={() => setIsAddingSkill(true)}
                        className="h-10 text-sm"
                    >
                        <Plus className="w-4 h-4 mr-1.5" />
                        Add Your First Skill
                    </Button>
                </div>
            ) : (
                <div className="space-y-3 md:space-y-4">
                    {highSkills.length > 0 && (
                        <div className="p-2.5 md:p-3 rounded-xl md:rounded-2xl bg-emerald-50/50 border border-emerald-100">
                            <div className="flex items-center gap-2 mb-2 px-1">
                                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                                <span className="text-[10px] md:text-xs font-bold text-emerald-700 uppercase tracking-wide">High Confidence</span>
                                <span className="text-[10px] md:text-xs text-emerald-500">({highSkills.length})</span>
                            </div>
                            <div className="space-y-1.5 md:space-y-2">
                                {highSkills.map((skill) => {
                                    const globalIdx = richSkills.findIndex(s => s === skill);
                                    return (
                                        <SkillRow
                                            key={skill.skill}
                                            skill={skill}
                                            onEdit={() => setEditingIndex(globalIdx)}
                                            onDelete={() => handleDeleteSkill(globalIdx)}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {mediumSkills.length > 0 && (
                        <div className="p-2.5 md:p-3 rounded-xl md:rounded-2xl bg-amber-50/50 border border-amber-100">
                            <div className="flex items-center gap-2 mb-2 px-1">
                                <div className="w-2 h-2 rounded-full bg-amber-500" />
                                <span className="text-[10px] md:text-xs font-bold text-amber-700 uppercase tracking-wide">Medium Confidence</span>
                                <span className="text-[10px] md:text-xs text-amber-500">({mediumSkills.length})</span>
                            </div>
                            <div className="space-y-1.5 md:space-y-2">
                                {mediumSkills.map((skill) => {
                                    const globalIdx = richSkills.findIndex(s => s === skill);
                                    return (
                                        <SkillRow
                                            key={skill.skill}
                                            skill={skill}
                                            onEdit={() => setEditingIndex(globalIdx)}
                                            onDelete={() => handleDeleteSkill(globalIdx)}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {lowSkills.length > 0 && (
                        <div className="p-2.5 md:p-3 rounded-xl md:rounded-2xl bg-red-50/50 border border-red-100">
                            <div className="flex items-center gap-2 mb-2 px-1">
                                <div className="w-2 h-2 rounded-full bg-red-400" />
                                <span className="text-[10px] md:text-xs font-bold text-red-700 uppercase tracking-wide">Low Confidence</span>
                                <span className="text-[10px] md:text-xs text-red-400">({lowSkills.length}) — review recommended</span>
                            </div>
                            <div className="space-y-1.5 md:space-y-2">
                                {lowSkills.map((skill) => {
                                    const globalIdx = richSkills.findIndex(s => s === skill);
                                    return (
                                        <SkillRow
                                            key={skill.skill}
                                            skill={skill}
                                            onEdit={() => setEditingIndex(globalIdx)}
                                            onDelete={() => handleDeleteSkill(globalIdx)}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <AnimatePresence>
                {isAddingSkill && (
                    <AddSkillForm
                        onAdd={handleAddSkill}
                        onCancel={() => setIsAddingSkill(false)}
                    />
                )}
            </AnimatePresence>

            {!isAddingSkill && (
                <Button
                    variant="outline"
                    onClick={() => setIsAddingSkill(true)}
                    className="mt-3 md:mt-4 h-9 md:h-10 text-xs md:text-sm w-full border-dashed border-slate-200 text-slate-500 hover:text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                >
                    <Plus className="w-3.5 h-3.5 md:w-4 md:h-4 mr-1.5" />
                    Add Missing Skill
                </Button>
            )}

            <div className="mt-3 md:mt-4 p-2.5 md:p-3 rounded-xl bg-blue-50 border border-blue-100">
                <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
                    <div>
                        <p className="text-[10px] md:text-xs font-bold text-blue-800">About Confidence Levels</p>
                        <p className="text-[10px] md:text-xs text-blue-600 mt-0.5 leading-relaxed">
                            Higher confidence skills are prioritized in job matching. Remove any skills that don't reflect your expertise.
                        </p>
                    </div>
                </div>
            </div>

            {richSkills.length === 0 && (
                <div className="mt-3 md:mt-4 p-2.5 md:p-3 rounded-xl bg-amber-50 border border-amber-200">
                    <div className="flex items-start gap-2">
                        <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                            <p className="text-[10px] md:text-xs font-bold text-amber-800">No Skills Added</p>
                            <p className="text-[10px] md:text-xs text-amber-600 mt-0.5 leading-relaxed">
                                Adding skills helps us find better job matches. You can add them later in your profile.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex gap-3 pt-4 mt-4">
                <Button type="button" variant="ghost" onClick={onPrev} className="h-11 rounded-xl font-bold text-slate-400 hover:text-slate-900 border border-slate-100 hover:bg-slate-50 text-sm px-4">
                    <ArrowLeft className="mr-2 h-4 w-4" />
                    Back
                </Button>
                <Button
                    type="button"
                    onClick={onNext}
                    disabled={isSaving}
                    className="flex-1 h-11 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 text-sm disabled:opacity-50 disabled:cursor-not-allowed group"
                >
                    {isSaving ? <LoadingSpinner size="sm" /> : (
                        <>
                            {richSkills.length === 0 ? "Skip for Now" : "Save & Continue"}
                            <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}
