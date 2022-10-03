//
//  ViewController.swift
//  Test v2
//
//  Created by Charlie on 27/09/2022.
//

import UIKit

class EventViewController: UIViewController {
    
    @IBOutlet weak var building: UILabel!
    @IBOutlet weak var dateTime: UILabel!
    @IBOutlet weak var name: UILabel!
    @IBOutlet weak var photo: UIImageView!
    
    let apiService = APIService()

    override func viewDidLoad() {
        super.viewDidLoad()
        
        apiService.callAPI { result in
            DispatchQueue.main.async { [self] in
                self.name.text = "\(result.rank)" + " " + "\(result.lastName)"
                self.dateTime.text = "\(result.date)" + " " + "\(result.time)"
                self.building.text = "\(result.building)"
                
                let url = URL(string:result.imageURL)
                let imagedata = NSData.init(contentsOf: url! )

                if imagedata != nil {
                    self.photo.image = UIImage(data:imagedata! as Data)
                }
            }
        }
    }

}

