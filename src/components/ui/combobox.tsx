"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "cmdk";

export function Combobox({ 
  options, 
  value, 
  onChange, 
  placeholder = "Select...", 
  emptyText = "No results found.",
  disabled = false,
  className
}: { 
  options: { value: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  emptyText?: string;
  disabled?: boolean;
  className?: string;
}) {
  const [open, setOpen] = React.useState(false);

  const selectedLabel = options.find((opt) => opt.value === value)?.label || placeholder;

  return (
    <PopoverPrimitive.Root open={open} onOpenChange={setOpen}>
      <PopoverPrimitive.Trigger asChild>
        <button
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "flex w-full items-center justify-between rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground shadow-sm hover:bg-muted/50 focus:outline-none focus:ring-1 focus:ring-accent disabled:cursor-not-allowed disabled:opacity-50",
            className
          )}
        >
          <span className="truncate">{selectedLabel}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </button>
      </PopoverPrimitive.Trigger>
      <PopoverPrimitive.Portal>
        <PopoverPrimitive.Content
          align="start"
          className="z-50 w-[var(--radix-popover-trigger-width)] min-w-[200px] overflow-hidden rounded-md border border-border bg-popover text-popover-foreground shadow-md outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2"
        >
          <Command className="flex h-full w-full flex-col overflow-hidden rounded-md bg-popover text-popover-foreground">
            <CommandInput 
              placeholder="Search..." 
              className="flex h-10 w-full rounded-md bg-transparent py-3 px-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50 border-b border-border"
            />
            <CommandList className="max-h-[300px] overflow-y-auto overflow-x-hidden">
              <CommandEmpty className="py-6 text-center text-sm">{emptyText}</CommandEmpty>
              <CommandGroup className="p-1 text-foreground">
                {options.map((option) => (
                  <CommandItem
                    key={option.value}
                    value={option.label}
                    onSelect={() => {
                      onChange(option.value);
                      setOpen(false);
                    }}
                    className="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none aria-selected:bg-accent/15 aria-selected:text-accent data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        value === option.value ? "opacity-100 text-accent" : "opacity-0"
                      )}
                    />
                    {option.label}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverPrimitive.Content>
      </PopoverPrimitive.Portal>
    </PopoverPrimitive.Root>
  );
}
