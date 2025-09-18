{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";

    systems.url = "github:nix-systems/default-linux";
    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  } @ inputs: let
    lib = nixpkgs.lib;
  in
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
      };
    in rec {
      formatter = pkgs.alejandra;
      packages = import ./pkgs {
        inherit pkgs;
      };
      devShells = {
        default = pkgs.mkShell {
          buildInputs = [
            packages.ramulator2
          ];
          nativeBuildInputs = with pkgs; [
            rustup
            uv
          ];
        };
      };
    });
}
