use std::mem::ManuallyDrop;
use std::sync::Arc;

use anyhow::Result;
use memory::MemoryTimingModel;
use runtime::{Executor, Instant};

#[tokio::main]
async fn main() -> Result<()> {
    let executor = Executor::new();

    let model = Arc::new(ManuallyDrop::new(ramulator::Ramulator::hbm2_preset(1)?));
    executor.spawn(async move {
        for offset in (0..1024 * 1024).step_by(64) {
            let model_clone = model.clone();
            Executor::current().spawn(async move {
                model_clone.read(offset).await;
                println!("{offset} {:?}", Executor::current().now());
            });
        }
    });

    executor.enter(Instant::ETERNITY).await;
    eprintln!("Simulation completed. Last instance {:?}", executor.now());
    Ok(())
}
