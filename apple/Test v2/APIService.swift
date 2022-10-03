//
//  ApiService.swift
//  Test v2
//
//  Created by Charlie on 27/09/2022.
//

import Foundation

class APIService {
    
    
    func callAPI(_ completionHandler: @escaping ( _ result: Person) -> Void) {
        
        
        completionHandler(Person.init(rank: "Cpl", lastName: "Hanks", date: "27/09/2022", time: "12:00", building: "Building 101", imageURL: "https://t5accessimages.s3.eu-west-2.amazonaws.com/iostest.jpg"))
        
        
//        guard let url = URL(string: "https://ddcfe160-2520-4284-90e2-dc2b9c41fea4.mock.pstmn.io/intruder") else { return }
//
//        URLSession.shared.dataTask(with: url) { data, response, error in
//
//            let decoder = JSONDecoder()
//
//            if let data = data{
//                do{
//                    let tasks = try decoder.decode(Person.self, from: data)
//                    completionHandler(tasks)
//                }catch{
//                    print(error)
//                }
//            }
//        }.resume()
    }
}


