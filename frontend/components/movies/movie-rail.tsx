"use client";

import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Movie } from "@/types";
import { MovieCard } from "./movie-card";

export function MovieRail({ title, movies, href, showReminder = false }: { title: string; movies: Movie[]; href?: string; showReminder?: boolean }) {
  const railRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const moved = useRef(false);
  const startX = useRef(0);
  const startScroll = useRef(0);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollState = useCallback(() => {
    const rail = railRef.current;
    if (!rail) return;
    setCanScrollLeft(rail.scrollLeft > 1);
    setCanScrollRight(rail.scrollLeft + rail.clientWidth < rail.scrollWidth - 1);
  }, []);

  useEffect(() => {
    updateScrollState();
    const rail = railRef.current;
    if (!rail) return;
    rail.addEventListener("scroll", updateScrollState, { passive: true });
    const observer = new ResizeObserver(updateScrollState);
    observer.observe(rail);
    return () => {
      rail.removeEventListener("scroll", updateScrollState);
      observer.disconnect();
    };
  }, [movies.length, updateScrollState]);

  const scrollByPage = (direction: number) => {
    railRef.current?.scrollBy({ left: direction * Math.max(280, railRef.current.clientWidth * 0.8), behavior: "smooth" });
  };

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    const rail = railRef.current;
    if (!rail) return;
    dragging.current = true;
    moved.current = false;
    startX.current = event.clientX;
    startScroll.current = rail.scrollLeft;
    rail.classList.add("cursor-grabbing");
  };

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const rail = railRef.current;
    if (!dragging.current || !rail) return;
    const distance = event.clientX - startX.current;
    if (Math.abs(distance) > 4) {
      if (!moved.current) rail.setPointerCapture(event.pointerId);
      moved.current = true;
    }
    rail.scrollLeft = startScroll.current - distance;
  };

  const stopDragging = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    dragging.current = false;
    if (railRef.current?.hasPointerCapture(event.pointerId)) railRef.current.releasePointerCapture(event.pointerId);
    railRef.current?.classList.remove("cursor-grabbing");
  };

  const preventClickAfterDrag = (event: React.MouseEvent<HTMLDivElement>) => {
    if (moved.current) {
      event.preventDefault();
      event.stopPropagation();
      moved.current = false;
    }
  };

  return <section className="mb-12">
    <div className="mb-5 flex items-end justify-between">
      <h2 className="text-xl font-semibold tracking-tight text-white sm:text-2xl">{title}</h2>
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {canScrollLeft && <button type="button" aria-label={`Scroll ${title} left`} onClick={() => scrollByPage(-1)} className="grid size-8 place-items-center rounded-full border border-white/15 text-white/80 transition hover:border-amber-200/70 hover:text-amber-200"><ArrowLeft size={16} /></button>}
          {canScrollRight && <button type="button" aria-label={`Scroll ${title} right`} onClick={() => scrollByPage(1)} className="grid size-8 place-items-center rounded-full border border-white/15 text-white/80 transition hover:border-amber-200/70 hover:text-amber-200"><ArrowRight size={16} /></button>}
        </div>
        {href && <Link href={href} className="flex items-center gap-1 text-sm text-amber-200 hover:text-amber-100">See all <ArrowRight size={15} /></Link>}
      </div>
    </div>
    <div ref={railRef} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={stopDragging} onPointerCancel={stopDragging} onClickCapture={preventClickAfterDrag} className="scrollbar-hide flex touch-pan-x select-none gap-4 overflow-x-auto overflow-y-hidden overscroll-x-contain pb-2 cursor-grab">
      {movies.map(movie => <MovieCard key={movie.id} movie={movie} compact showReminder={showReminder} />)}
    </div>
  </section>;
}

export function MovieGrid({ movies, showReminder = false }: { movies: Movie[]; showReminder?: boolean }) { return <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">{movies.map(movie => <MovieCard key={movie.id} movie={movie} showReminder={showReminder} />)}</div>; }
