"use client";
import { PageHeading, PageShell } from "@/components/common/page-shell";
import { EmptyState, ErrorState, SkeletonGrid } from "@/components/common/states";
import { MovieGrid } from "@/components/movies/movie-rail";
import { useInteractions } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth/context";
import { useRouter } from "next/navigation";
export default function WatchlistPage(){const {user}=useAuth();const router=useRouter();const {watchlist}=useInteractions();if(!user)return <PageShell><EmptyState title="Sign in to see your watchlist" action={<button onClick={()=>router.push('/login')} className="rounded-full bg-amber-300 px-5 py-2 font-semibold text-black">Sign in</button>}/></PageShell>;return <PageShell><PageHeading eyebrow="Your shelf" title="Watchlist" description="Keep the films you want to return to close at hand." />{watchlist.isLoading?<SkeletonGrid count={10}/>:watchlist.isError?<ErrorState message="Your watchlist could not be loaded."/>:watchlist.data.items.length?<MovieGrid movies={watchlist.data.items.map(x=>x.movie)}/>:<EmptyState title="Your watchlist is waiting for its first film" action={<button onClick={()=>router.push('/movies')} className="rounded-full bg-amber-300 px-5 py-2 font-semibold text-black">Browse movies</button>}/>}</PageShell>}
