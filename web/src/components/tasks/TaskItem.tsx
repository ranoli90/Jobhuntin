import { motion, AnimatePresence } from "framer-motion";
import { Check, Flag, Clock, MoreHorizontal } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const priorityColors = {
  high: "bg-red-500/10 text-red-500",
  medium: "bg-amber-500/10 text-amber-500",
  low: "bg-blue-500/10 text-blue-500",
} as const;

const priorityIcons = {
  high: <Flag className="h-3 w-3" />,
  medium: <Flag className="h-3 w-3" />,
  low: <Flag className="h-3 w-3" />,
} as const;

type Priority = keyof typeof priorityColors;

type Task = {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  priority: Priority;
  dueDate?: string;
  category?: string;
};

type TaskItemProps = {
  task: Task;
  onToggleComplete: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (task: Task) => void;
};

export function TaskItem({ task, onToggleComplete, onDelete, onEdit }: TaskItemProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleComplete(task.id);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={cn(
        "group relative overflow-hidden rounded-xl border border-white/5 bg-white/5 p-4 backdrop-blur-sm transition-all hover:bg-white/10",
        task.completed && "opacity-60"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Priority indicator */}
      <div className="absolute left-0 top-0 h-full w-1.5 bg-gradient-to-b from-transparent to-transparent">
        <motion.div
          className={cn(
            "h-full w-full",
            priorityColors[task.priority],
            task.completed && "opacity-30"
          )}
          initial={{ height: 0 }}
          animate={{ height: task.completed ? '100%' : '100%' }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        />
      </div>

      <div className="relative pl-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <button
              onClick={handleComplete}
              className={cn(
                "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-all",
                task.completed
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-500"
                  : "border-white/20 hover:border-emerald-500/50 hover:bg-emerald-500/10"
              )}
            >
              {task.completed && <Check className="h-3 w-3" />}
            </button>
            <div>
              <h3
                className={cn(
                  "text-sm font-medium leading-tight text-white transition-all",
                  task.completed && "text-white/60 line-through"
                )}
              >
                {task.title}
              </h3>
              {task.description && (
                <p className="mt-1 text-xs text-white/60">{task.description}</p>
              )}
              <div className="mt-2 flex items-center gap-3">
                {task.dueDate && (
                  <div className="flex items-center gap-1 text-xs text-white/50">
                    <Clock className="h-3 w-3" />
                    <span>{task.dueDate}</span>
                  </div>
                )}
                {task.category && (
                  <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-white/60">
                    {task.category}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="relative">
            <button
              onClick={(e: React.MouseEvent<HTMLButtonElement>) => {
                e.stopPropagation();
                setShowMenu(!showMenu);
              }}
              className="rounded-full p-1 text-white/40 hover:bg-white/5 hover:text-white/70"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            
            <AnimatePresence>
              {showMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 10, scale: 0.95 }}
                  className="absolute right-0 z-10 mt-1 w-40 origin-top-right rounded-lg bg-gray-900/95 p-1 shadow-xl ring-1 ring-white/10 backdrop-blur-xl"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    onClick={() => onEdit(task)}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-white/80 hover:bg-white/5"
                  >
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => onDelete(task.id)}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-red-400 hover:bg-red-500/10"
                  >
                    <span>Delete</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
      
      {/* Subtle hover effect */}
      <motion.div
        className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-r from-transparent to-white/5 opacity-0"
        animate={{ opacity: isHovered ? 1 : 0 }}
        transition={{ duration: 0.2 }}
      />
    </motion.div>
  );
}
