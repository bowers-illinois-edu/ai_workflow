---
name: campus-computing
description: Choose a machine for a long computation (Jake's laptop, koelsch, keeling, or the Illinois campus cluster), then write a Slurm job script, submit it, and watch the jobs overnight. Use whenever a simulation, permutation run, or power analysis would loop over redrawn assignments or simulated datasets, and whenever the conversation mentions the campus cluster, keeling, koelsch, lager, porter, Slurm, sbatch, squeue, a job array, a held or pending job, or a run left going overnight.
---

# Using koelsch, keeling, and the campus cluster for long runs

Jake Bowers wants simulations and permutation runs to finish as early as
possible without running on his laptop. This file records what we
learned on 7 and 8 November 2026, when six campus cluster jobs failed
to start for sixteen hours and the work moved to keeling and back. It
is written for the next assistant that has to choose a machine, write
a job script, or watch jobs overnight. Every number below was read
from the machines or their documentation on 8 November 2026. Check
them again with the commands given before relying on them.

This file is `skills/campus-computing/SKILL.md` in the repository
`~/repos/ai_workflow`. When you find that a number or a rule here is
wrong or out of date, tell Jake and propose the change to this file. The
repository is public on GitHub, so keep passwords, Duo codes, and tokens
out of the file.

## Which machine for which job

1. Jake's laptop runs tests, renders, and computations of a few
   seconds. Nothing that loops over redrawn assignments or simulated
   datasets. A 100,000-draw run filled its 36 GB on 7 November.
2. Koelsch, lager, and porter are single machines with no scheduler.
   Koelsch has 40 cores and 251 GB (`ssh koelsch-lager`). A run there
   starts at once and suits one job of a few hours. Start it under
   `nohup` and write a log that ends with a line beginning `finished`,
   so a watcher can tell a finished run from a dead one.
3. Keeling is a Slurm cluster where Jake owns four nodes, keeling-h22
   to h25, with 24 cores and 256 GB each (`ssh keeling-lager`,
   partition `jwbowers`, account `pol-jwbowers-group`). No other user
   competes for them, so a job starts as soon as a node is free. It
   needs no Duo login, so jobs there can be watched while Jake's laptop
   is asleep or closed. The container image and a checkout are at
   `/data/keeling/a/jwbowers/images` and
   `/data/keeling/a/jwbowers/repos/block_test_power`.
4. The campus cluster (`ssh cc`) has far more cores than keeling but is
   shared. The connection needs Jake's password and Duo, typed by him,
   and it closes when the laptop sleeps. After that, no command reaches
   the cluster until he logs in again.

## The campus cluster's partitions

`sinfo -s` lists the partitions Jake's accounts can use, and
`scontrol show partition <name>` gives each one's limits. On 8
November:

1. IllinoisComputes (account `jwbowers-ic`): 22 nodes of 128 cores and
   512 GB, a limit of 3 days per job, and a default of 3.8 GB of memory
   per core when a job does not ask for memory. It is busy. At 10:50 on
   a Sunday it had 113 jobs waiting and 252 running, and Slurm
   estimated that a new job of five 64-core tasks would start at 20:31.
2. secondary: 138 nodes of mixed age, a limit of 4 hours per job, open
   to every account. The nodes range from 40 cores and 192 GB (Intel
   Xeon Gold 6248, 2019) to 128 cores and 256 to 512 GB (AMD EPYC 7713
   and Intel Xeon 8358). Slurm never places a job on a node with
   fewer cores than the job asks for. Its jobs can be preempted, and
   a preempted job goes back in the queue and starts over from the
   beginning. When the same five tasks were allowed to run in
   secondary as well, four started within a minute.
3. ic-express (1 node, 8 hours) refused our account with the reason
   `PartitionConfig`; it admits only the accounts
   `acc-illinoiscomputes` and `acc-ncsa`. scavenger (1 day) can stop a
   job two minutes after it starts, so a job there loses its work
   unless it saves checkpoints.
4. Each account may have 40 jobs running at once.

So the secondary queue is useful, with one condition. A task that
might exceed 4 hours is killed at 4 hours and its work is lost, so
split the work until each task's expected time is at most about 2
hours, half the limit. That margin covers a slower node and a restart
after preemption. Then submit to both partitions with
`--partition=IllinoisComputes,secondary`, and Slurm starts each task in
whichever has room first. Expected times come from an earlier run's
logs. For the Sarkar and Coppock power analysis at 10,000 simulated
datasets and 10,000 redrawn assignments, one comparison of 944
respondents took 5,340 seconds on 24 cores, and the time grows a
little faster than the number of respondents.

## How to write and submit a job script

1. Put every setting of the run in the job script, and submit it bare:
   `sbatch script.sbatch`. Do not pass settings with
   `--export=ALL,VAR=value`. The sbatch manual says a variable list in
   `--export` acts "as if --get-user-env was defined", which makes
   Slurm open a login shell as the user on the compute node, and "if
   the user environment retrieval fails or times out, the job will be
   aborted, requeued and held." All six jobs submitted that way on 7
   November failed with the reason `user env retrieval failed requeued
   held`, again after every release, while jobs submitted without
   `--export` ran in the same partition over the same hours. The job array described next,
   submitted with no `--export`, started at once.
2. To split one run into parts, use a job array (`#SBATCH --array=1-5`)
   and let the script pick its part from `SLURM_ARRAY_TASK_ID`, from a
   table of settings written in the script.
   `Analysis/sarkar_coppock/power_choice_array.sbatch` in
   block_test_power does this.
3. Ask for the memory the job was measured to need, plus room to
   spare. Measure it with `sstat -j <job> -o MaxRSS` while a job runs, or
   `sacct -j <job> -o MaxRSS` after. The power analysis used about 1 GB
   per parallel worker, so 64 workers get `--mem=96G`. Without `--mem`,
   IllinoisComputes gives 3.8 GB per core, 243 GB for 64 cores, which
   rules out the 256 GB nodes. The campus cluster guide warns that a
   memory request no node in the partition can meet leaves the job
   waiting forever, and that about 90 percent of a node's memory is
   usable.
4. Ask for a time limit near the expected time, not the partition's
   maximum. A short limit lets Slurm start the job in gaps between
   other jobs, and it is required for secondary.
5. Create the folder named in `#SBATCH --output` before submitting.
   Slurm does not create it. Without it the job fails and leaves no log.
6. Commit the code and pull it into the cluster's checkout first. The
   job scripts refuse to run in a checkout with uncommitted changes to
   tracked files, so the log's commit line names the code that ran.
7. Make each job resumable. The power analysis driver skips every
   comparison already in its output file, so a job that is killed or
   preempted loses only the comparison it was working on.

## Holds and how to watch jobs overnight

1. A job requeued with the word `held` in its reason never starts again
   until someone runs `scontrol release <job>`. After a job has failed
   to launch several times, Slurm gives it the reason `launch failure
   limit exceeded requeued held`, which only an administrator can
   release. Then cancel it and resubmit, on another partition or
   machine.
2. A watcher is a shell loop on the laptop that every 5 or 10 minutes
   runs `squeue` and `sacct` over ssh, releases a held job up to three
   times, and exits with a one-line reason when a job ends in any
   state other than COMPLETED, when every job has finished, or when it
   has lost contact for an hour. Run it in the background so its exit
   wakes the assistant. Start it under `caffeinate -i`, which keeps the
   laptop from sleeping when idle. Closing the lid still sleeps it, so
   for a campus cluster run Jake has to leave the laptop plugged in
   with the lid open.
3. Inside a `while read` loop, give every `ssh` the `-n` option.
   Without it, ssh reads the rest of the loop's input, and the loop
   skips jobs.
4. When the same work runs in two places as insurance, write each to
   its own output folder, and cancel the slower copy once the faster
   one has finished.

## What happened on 7 and 8 November

Six jobs of 32 cores and 128 GB each were submitted to IllinoisComputes
at 13:30 on 7 November with `--export=ALL,...`. From 14:39 every launch
failed and was held. A watcher released them twelve times overnight
until three reached the hold users cannot release, at 06:35. The six
parts then ran on keeling's four nodes from 06:37, two of them waiting
for a free node. At 10:51 the five largest comparisons were resubmitted
to the campus cluster as a job array with no `--export`, 64 cores and
96 GB each, allowed into IllinoisComputes or secondary. Four started in
secondary within a minute. Copies of the two largest also wait on
keeling.
