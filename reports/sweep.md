# Sweep (validation only; held-out systems untouched)

A validation line is worth about 1.7 points, so a gap under 0.034 (two lines) is noise.

val_pa tops out near 0.93 here (the last wrong lines are label conventions), so runs that tie on val_pa are ranked by the lower validation loss.

| run | best val_pa | vs default | best step | macro at best | last val_pa | min eval_loss | min | peak GB |
|---|---|---|---|---|---|---|---|---|
| default | 0.931 |  | 76 | 0.910 | 0.931 | 0.0424 | 8.1 | 7.4 |
| r8 | 0.914 | -0.017 (noise) | 114 | 0.894 | 0.914 | 0.0529 | 8.7 | 7.4 |
| r32 | 0.948 | +0.017 (noise) | 76 | 0.920 | 0.931 | 0.0369 | 7.9 | 7.5 |
| lr1e-4 | 0.845 | -0.086 | 76 | 0.843 | 0.845 | 0.0693 | 3.4 | 7.4 |
| lr5e-4 | 0.948 | +0.017 (noise) | 95 | 0.920 | 0.948 | 0.0399 | 8.1 | 7.4 |
| ep1 | 0.690 | -0.241 | 19 | 0.679 | 0.690 | 0.1404 | 3.7 | 7.4 |
| ep5 | 0.948 | +0.017 (noise) | 114 | 0.920 | 0.948 | 0.0345 | 11.5 | 7.4 |
| all_linear | 0.931 | +0.000 (noise) | 76 | 0.907 | 0.931 | 0.0263 | 13.4 | 7.6 |
| no_system | 0.879 | -0.052 | 76 | 0.883 | 0.879 | 0.0465 | 7.6 | 7.4 |

## val_pa per system at the best step

| run | BGL | HDFS | HPC | Hadoop | HealthApp | Linux | OpenSSH | Spark | Zookeeper |
|---|---|---|---|---|---|---|---|---|---|
| default | 1.00 | 0.50 | 1.00 | 0.82 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| r8 | 1.00 | 0.50 | 0.86 | 0.82 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| r32 | 1.00 | 0.50 | 1.00 | 0.91 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| lr1e-4 | 1.00 | 0.50 | 0.57 | 0.64 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| lr5e-4 | 1.00 | 0.50 | 1.00 | 0.91 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| ep1 | 0.83 | 0.50 | 0.57 | 0.45 | 1.00 | 0.75 | 0.50 | 0.50 | 1.00 |
| ep5 | 1.00 | 0.50 | 1.00 | 0.91 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |
| all_linear | 1.00 | 0.50 | 1.00 | 0.91 | 1.00 | 0.75 | 1.00 | 1.00 | 1.00 |
| no_system | 0.75 | 0.50 | 1.00 | 0.82 | 1.00 | 0.88 | 1.00 | 1.00 | 1.00 |

## Conclusion

We keep the default config (`configs/qwen3_4b_r16.yaml`); no `configs/best.yaml` was made. Three runs
fall clearly short of it: one epoch, lr 1e-4, and no system line (-3 lines, always on
`generating core.<*>`). Rank 8 to 32, lr 2e-4 to 5e-4, 3 to 5 epochs and q/v to all linear layers
all land within one line of the default, which is noise on 58 lines. The lower validation
loss of r32, ep5 and all_linear costs more compute and does not show up in val_pa. HDFS stays at
0.50 in every run: its two lines carry label conventions (collapsed lists) that no setting
fixes. So the sweep is a sensitivity check, not a tuning win. `system_line` stays on.

Not tested: combinations of axes (a confirmation run). Nothing beat the default beyond noise,
so there was no winner per axis to combine. Validation here follows template-disjoint
generalization; it does not predict performance on unseen systems.
