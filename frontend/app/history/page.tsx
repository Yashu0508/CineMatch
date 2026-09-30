"use client";
import { PageHeading, PageShell } from "@/components/common/page-shell";
import { EmptyState, ErrorState, SkeletonGrid } from "@/components/common/states";
import { MovieGrid } from "@/components/movies/movie-rail";
import { useInteractions } from "@/hooks/use-api";
import { useAuth } from "@/lib/auth/context";
import { useRouter } from "next/navigation";
export default function HistoryPage(){const {user}=useAuth();const router=useRouter();const {history}=useInteractions();if(!user)return <PageShell><EmptyState title="Sign in to see your viewing history" action={<button onClick={()=>router.push('/login')} className="rounded-full bg-amber-300 px-5 py-2 font-semibold text-black">Sign in</button>}/></PageShell>;return <PageShell><PageHeading eyebrow="Your journey" title="History" description="The stories you have marked as watched live here." />{history.isLoading?<SkeletonGrid count={10}/>:history.isError?<ErrorState message="Your history could not be loaded."/>:history.data.items.length?<MovieGrid movies={history.data.items.map(x=>x.movie)}/>:<EmptyState title="No watched movies yet" action={<button onClick={()=>router.push('/movies')} className="rounded-full bg-amber-300 px-5 py-2 font-semibold text-black">Find something to watch</button>}/>}</PageShell>}
